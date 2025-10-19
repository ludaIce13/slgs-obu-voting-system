from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask import current_app, send_from_directory
from . import db
from .models import Voter, Candidate, Vote, Position
from .models import Setting
from datetime import datetime, timedelta
import csv
import io
import json
import os
from werkzeug.utils import secure_filename
from collections import defaultdict

main = Blueprint('main', __name__)
admin = Blueprint('admin', __name__, url_prefix='/admin')

# Simple rate limiting for vote attempts
vote_attempts = defaultdict(list)
RATE_LIMIT_WINDOW = timedelta(minutes=5)
MAX_ATTEMPTS_PER_WINDOW = 10

@main.route('/')
def index():
    # Provide current voting status to the public home page
    try:
        voting_open = False
        voting_setting = Setting.query.filter_by(key='voting_open').first()
        voting_until_setting = Setting.query.filter_by(key='voting_until').first()
        if voting_setting and voting_setting.value == 'true':
            voting_open = True
        voting_until = voting_until_setting.value if voting_until_setting else None
    except Exception:
        voting_open = False
        voting_until = None

    return render_template('index.html', voting_open=voting_open, voting_until=voting_until)

@main.route('/vote', methods=['GET', 'POST'])
def vote():
    client_ip = request.remote_addr

    # Update voting state if until timestamp passed
    try:
        def _update_voting_state_if_needed():
            vs = Setting.query.filter_by(key='voting_open').first()
            vu = Setting.query.filter_by(key='voting_until').first()
            if vu:
                import datetime
                try:
                    until_dt = datetime.datetime.fromisoformat(vu.value)
                except Exception:
                    # If parsing fails, don't auto-close
                    return
                if datetime.datetime.utcnow() > until_dt:
                    # Time passed, close voting
                    if vs:
                        vs.value = 'false'
                    try:
                        db.session.delete(vu)
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

        _update_voting_state_if_needed()
    except Exception:
        pass

    # Check voting status setting
    try:
        voting_open = False
        voting_setting = Setting.query.filter_by(key='voting_open').first()
        if voting_setting and voting_setting.value == 'true':
            voting_open = True
    except Exception:
        voting_open = False

    if not voting_open:
        return render_template('vote.html', positions=[], error='Voting is currently closed.'), 403

    if request.method == 'POST':
        voter_id = request.form.get('voter_id')
        voting_token = request.form.get('voting_token')
        print(f"VOTE ATTEMPT - IP: {client_ip}, Voter ID: {voter_id}, Token: {voting_token[:8]}...")

        # Rate limiting check
        now = datetime.utcnow()
        # Clean old attempts
        vote_attempts[client_ip] = [attempt for attempt in vote_attempts[client_ip]
                                   if now - attempt < RATE_LIMIT_WINDOW]

        if len(vote_attempts[client_ip]) >= MAX_ATTEMPTS_PER_WINDOW:
            print(f"RATE LIMITED - IP: {client_ip}, Attempts: {len(vote_attempts[client_ip])}")
            flash('Too many voting attempts. Please wait 5 minutes before trying again.', 'error')
            return redirect(url_for('main.vote'))

        # Record this attempt
        vote_attempts[client_ip].append(now)

        # Validate inputs
        if not voter_id:
            flash('Please enter your Voter ID.', 'error')
            return redirect(url_for('main.vote'))

        if not voting_token:
            flash('Please enter your Voting Token.', 'error')
            return redirect(url_for('main.vote'))

        # Validate Voter ID format (accepts OBUSLG001 format or Member ID format, 3-20 characters)
        if not (len(voter_id) >= 3 and len(voter_id) <= 20 and all(c.isalnum() or c == '-' for c in voter_id)):
            print(f"VOTE REJECTED - Invalid Voter ID format: {voter_id}")
            flash('Voter ID must be 3-20 characters (alphanumeric and dashes only, e.g., OBUSLG001).', 'error')
            return redirect(url_for('main.vote'))

        # Validate Voting Token format (must be exactly 8 digits)
        if not (voting_token.isdigit() and len(voting_token) == 8):
            print(f"VOTE REJECTED - Invalid Voting Token format: {voting_token}")
            flash('Voting Token must be exactly 8 digits.', 'error')
            return redirect(url_for('main.vote'))

        # Find voter by both Voter ID and Voting Token
        try:
            voter = Voter.query.filter_by(voter_id=voter_id, voting_token=voting_token).first()
            print(f"VOTE VALIDATION - Voter found: {voter is not None}")
        except Exception as voter_error:
            print(f"Voter query error (likely missing voting_token column): {voter_error}")
            # Try to find voter by voter_id only
            try:
                voter = Voter.query.filter_by(voter_id=voter_id).first()
                print(f"VOTE VALIDATION - Voter found (without token): {voter is not None}")
                if voter:
                    print("WARNING: voting_token column missing, using voter_id only")
            except Exception as fallback_error:
                print(f"Fallback voter query also failed: {fallback_error}")
                voter = None

        if not voter:
            print(f"VOTE REJECTED - Voter ID/Token combination not found: {voter_id}")
            flash('Invalid Voter ID or Voting Token combination.', 'error')
            return redirect(url_for('main.vote'))

        if voter.has_voted:
            print(f"VOTE REJECTED - Voter already voted: {voter_id}")
            flash('This Voter ID has already been used.', 'error')
            return redirect(url_for('main.vote'))

        # Get positions that have voting enabled and have candidates
        all_positions = Position.query.all()
        positions = [pos for pos in all_positions if pos.voting_enabled and pos.candidates]
        votes_recorded = 0

        for position in positions:
            candidate_id = request.form.get(f'position_{position.id}')
            if candidate_id:
                candidate = Candidate.query.get(candidate_id)
                if candidate and candidate.position_id == position.id:
                    # Record the vote
                    vote = Vote(
                        voter_id=voter.id,
                        candidate_id=candidate.id,
                        position_id=position.id,
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    db.session.add(vote)
                    votes_recorded += 1

        # For this election, voters should vote for both positions, but we'll be flexible
        if votes_recorded == 0:
            flash('Please select at least one candidate for the available positions.', 'error')
            return redirect(url_for('main.vote'))

        # Mark voter as voted
        voter.has_voted = True
        db.session.commit()

        print(f"VOTE SUCCESS - Voter {voter.full_name} ({voter_id}) voted successfully")
        flash('Your votes have been recorded successfully!', 'success')
        return redirect(url_for('main.thank_you'))

    try:
        # Get positions that have voting enabled and have candidates
        all_positions = Position.query.all()
        # Only show positions where voting is enabled and have candidates
        votable_positions = [pos for pos in all_positions if pos.voting_enabled and pos.candidates]

        print(f"Vote page loaded - Found {len(all_positions)} total positions, {len(votable_positions)} votable with candidates")
        return render_template('vote.html', positions=votable_positions)
    except Exception as e:
        print(f"Error loading vote page: {e}")
        import traceback
        traceback.print_exc()
        # Return a simple error page instead of crashing
        return f"<h1>Error loading voting page</h1><p>Please contact the administrator. Error: {str(e)}</p>", 500

@main.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

@admin.route('/', methods=['GET'])
def admin_dashboard():
    # Check authorization from header, cookie, or query parameter
    token = (request.headers.get('Authorization') or
             request.cookies.get('admin_token') or
             request.args.get('token'))

    expected_token = os.environ.get('ADMIN_TOKEN', 'admin-token')

    # For debugging, allow access if token matches or if debug=true is passed
    debug_mode = request.args.get('debug') == 'true'
    auth_ok = (token == f'Bearer {expected_token}' or
               token == expected_token or
               debug_mode or
               expected_token == 'admin-token')  # Allow default token

    # Debug logging
    print(f"Admin dashboard access - Token: {token}, Expected: {expected_token}, Debug: {debug_mode}, Auth OK: {auth_ok}")

    if auth_ok:
        try:
            # Get voter statistics - handle missing voting_token column gracefully
            try:
                total_voters = Voter.query.count()
                voted_count = Voter.query.filter_by(has_voted=True).count()
            except Exception as voter_error:
                print(f"Voter query error (likely missing voting_token column): {voter_error}")
                # Try a more basic query without voting_token
                try:
                    total_voters = db.session.execute(db.text("SELECT COUNT(*) FROM voter")).scalar()
                    voted_count = db.session.execute(db.text("SELECT COUNT(*) FROM voter WHERE has_voted = true")).scalar()
                except Exception as fallback_error:
                    print(f"Fallback query also failed: {fallback_error}")
                    total_voters = 0
                    voted_count = 0

            # Get positions and candidates - show all positions but highlight voting status
            try:
                all_positions = Position.query.all()
                positions = all_positions  # Show all positions in admin
                candidates = Candidate.query.all()
            except Exception as e:
                print(f"Error loading positions/candidates: {e}")
                positions = []
                candidates = []

            # Get voters for display - handle missing voting_token column
            try:
                voters = Voter.query.all()
            except Exception:
                # Try without voting_token column
                try:
                    voters_result = db.session.execute(db.text("SELECT id, member_id, full_name, phone_number, voter_id, has_voted, created_at FROM voter"))
                    voters = []
                    for row in voters_result:
                        # Create a mock voter object with available fields
                        class MockVoter:
                            def __init__(self, data):
                                self.id = data[0]
                                self.member_id = data[1]
                                self.full_name = data[2]
                                self.phone_number = data[3]
                                self.voter_id = data[4]
                                self.has_voted = data[5]
                                self.created_at = data[6]
                                self.voting_token = "N/A (column missing)"

                        voters.append(MockVoter(row))
                except Exception as e:
                    print(f"Could not fetch voters: {e}")
                    voters = []

            # Get vote counts by position
            position_results = {}
            try:
                for position in positions:
                    position_candidates = Candidate.query.filter_by(position_id=position.id).all()
                    position_results[position.name] = {c.name: len(c.votes) for c in position_candidates}
            except Exception as e:
                print(f"Error getting vote counts: {e}")
                position_results = {}

            print(f"Authorized view - Voters: {total_voters}, Positions: {len(positions)}, Candidates: {len(candidates)}")

            # Debug: List all positions found
            if positions:
                print("Positions found:")
                for pos in positions:
                    print(f"  - {pos.name} (ID: {pos.id})")
            else:
                print("WARNING: No positions found in database!")
                print("Attempting to create positions...")

                # Try to create positions if none exist
                try:
                    # Create all 12 positions for the General Election
                    positions_data = [
                        ('President', True), ('Vice President', True), ('Secretary', True),
                        ('Assistant Secretary', False), ('Treasurer', False), ('Assistant Treasurer', False),
                        ('Social & Organizing Secretary', False), ('Assistant Social Secretary & Organizing Secretary', False),
                        ('Publicity Secretary', False), ('Chairman Improvement Committee', False),
                        ('Diaspora Coordinator', False), ('Chief Whip', False)
                    ]

                    for name, voting_enabled in positions_data:
                        # Check if position already exists
                        existing = Position.query.filter_by(name=name).first()
                        if not existing:
                            pos = Position(
                                name=name,
                                description=f'{name} of SLGS Old Boys Union',
                                voting_enabled=voting_enabled
                            )
                            db.session.add(pos)

                    db.session.commit()
                    print(f"Created {len(positions_data)} positions successfully")

                    # Refresh positions list
                    positions = Position.query.all()
                    print(f"Refreshed positions: now have {len(positions)} positions")

                except Exception as e:
                    print(f"Failed to create positions: {e}")

        except Exception as e:
            print(f"Error loading admin dashboard data: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to empty data if database queries fail
            total_voters = 0
            voted_count = 0
            positions = []
            candidates = []
            voters = []
            position_results = {}
            print("Fallback to empty data due to database error")
    else:
        total_voters = 0
        voted_count = 0
        positions = []
        candidates = []
        voters = []
        position_results = {}
        print("Unauthorized view - showing empty data")

    return render_template('admin.html',
                            total_voters=total_voters,
                            voted_count=voted_count,
                            positions=positions,
                            candidates=candidates,
                            voters=voters,
                            position_results=position_results,
                            auth_ok=auth_ok)

@admin.route('/debug')
def admin_debug():
    """Debug endpoint to show voter data without authorization"""
    total_voters = Voter.query.count()
    voted_count = Voter.query.filter_by(has_voted=True).count()
    positions = Position.query.all()
    candidates = Candidate.query.all()
    voters = Voter.query.all()

    # Get vote counts by position
    position_results = {}
    for position in positions:
        position_candidates = Candidate.query.filter_by(position_id=position.id).all()
        position_results[position.name] = {c.name: len(c.votes) for c in position_candidates}

    print(f"DEBUG ENDPOINT - Voters: {total_voters}, Positions: {len(positions)}")

    return render_template('admin.html',
                             total_voters=total_voters,
                             voted_count=voted_count,
                             positions=positions,
                             candidates=candidates,
                             voters=voters,
                             position_results=position_results,
                             auth_ok=True)


@main.route('/dashboard')
def public_dashboard():
    """Public election dashboard showing live results"""
    try:
        # Get voter statistics
        total_voters = Voter.query.count()
        voted_count = Voter.query.filter_by(has_voted=True).count()

        # Get positions that have voting enabled and have candidates
        all_positions = Position.query.all()
        positions = [pos for pos in all_positions if pos.voting_enabled and pos.candidates]
        position_results = {}

        for position in positions:
            position_results[position.name] = {}
            for candidate in position.candidates:
                vote_count = Vote.query.filter_by(position_id=position.id, candidate_id=candidate.id).count()
                position_results[position.name][candidate.name] = vote_count

        return render_template('dashboard.html',
                              total_voters=total_voters,
                              voted_count=voted_count,
                              positions=positions,
                              position_results=position_results)

    except Exception as e:
        print(f"Error loading public dashboard: {e}")
        # Return a simple error page instead of crashing
        return f"<h1>Error loading dashboard</h1><p>Please contact the administrator. Error: {str(e)}</p>", 500


# Voting control endpoints
@admin.route('/voting-status')
def voting_status():
    """Return current voting status and countdown if set."""
    try:
        # Auto-close if voting_until passed
        vu = Setting.query.filter_by(key='voting_until').first()
        if vu:
            import datetime
            try:
                until_dt = datetime.datetime.fromisoformat(vu.value)
                if datetime.datetime.utcnow() > until_dt:
                    vs = Setting.query.filter_by(key='voting_open').first()
                    if vs:
                        vs.value = 'false'
                        db.session.commit()
                    db.session.delete(vu)
                    db.session.commit()
            except Exception:
                pass

        vs = Setting.query.filter_by(key='voting_open').first()
        until = Setting.query.filter_by(key='voting_until').first()
        return jsonify({
            'voting_open': vs.value == 'true' if vs else False,
            'voting_until': until.value if until else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin.route('/voting-control', methods=['POST'])
def voting_control():
    """Open or close voting. POST payload: {'action': 'open'|'close', 'minutes': <int> (optional)}"""
    if not request.headers.get('Authorization') == 'Bearer ' + os.environ.get('ADMIN_TOKEN', 'admin-token'):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    action = data.get('action')
    minutes = int(data.get('minutes', 0)) if data.get('minutes') else 0

    try:
        if action == 'open':
            # Set voting_open and optionally voting_until
            vs = Setting.query.filter_by(key='voting_open').first()
            if not vs:
                vs = Setting(key='voting_open', value='true')
                db.session.add(vs)
            else:
                vs.value = 'true'

            if minutes > 0:
                import datetime
                until_time = (datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)).isoformat()
                vu = Setting.query.filter_by(key='voting_until').first()
                if not vu:
                    vu = Setting(key='voting_until', value=until_time)
                    db.session.add(vu)
                else:
                    vu.value = until_time
            else:
                # Clear voting_until
                vu = Setting.query.filter_by(key='voting_until').first()
                if vu:
                    db.session.delete(vu)

            db.session.commit()
            return jsonify({'message': 'Voting opened'}), 200

        elif action == 'close':
            vs = Setting.query.filter_by(key='voting_open').first()
            if vs:
                vs.value = 'false'
            vu = Setting.query.filter_by(key='voting_until').first()
            if vu:
                db.session.delete(vu)
            db.session.commit()
            return jsonify({'message': 'Voting closed'}), 200

        else:
            return jsonify({'error': 'Invalid action'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main.route('/favicon.ico')
def favicon():
    """Handle favicon requests"""
    return '', 204


@main.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files from the instance/uploads directory."""
    upload_dir = os.path.join(current_app.instance_path, 'uploads')
    # Security: ensure path is within upload_dir
    safe_path = os.path.join(upload_dir, filename)
    if not os.path.exists(safe_path):
        return '', 404
    return send_from_directory(upload_dir, filename)


@main.route('/_health')
def health():
    """Simple health check endpoint that verifies DB connectivity."""
    try:
        # Simple lightweight DB check
        db.session.execute('SELECT 1')
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        # Return error details for debugging (do not expose in production)
        return jsonify({'status': 'error', 'detail': str(e)}), 500

@admin.route('/upload-voters', methods=['POST'])
def upload_voters():
    """Upload voters from CSV file with comprehensive error handling"""
    try:
        # More flexible authorization check - accept multiple formats
        auth_header = request.headers.get('Authorization', '')
        cookie_token = request.cookies.get('admin_token', '')
        expected_token = os.environ.get('ADMIN_TOKEN', 'admin-token')

        # Check for Bearer token, direct token, or cookie token
        authorized = False
        if auth_header.startswith('Bearer '):
            provided_token = auth_header[7:]  # Remove 'Bearer ' prefix
            authorized = provided_token == expected_token
        elif auth_header == expected_token:
            authorized = True
        elif cookie_token == expected_token:
            authorized = True
        elif expected_token == 'admin-token':  # Allow default token for debugging
            authorized = True

        print(f"Upload auth check - Header: '{auth_header}', Cookie: '{cookie_token}', Expected: '{expected_token}', Authorized: {authorized}")

        if not authorized:
            return jsonify({'error': 'Unauthorized'}), 401

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file or not file.filename.endswith('.csv'):
            return jsonify({'error': 'Invalid file format. Please upload a CSV file.'}), 400

        # Process CSV file
        try:
            # Read file content with better error handling
            file_content = file.stream.read().decode("UTF8")
            stream = io.StringIO(file_content, newline=None)
            csv_input = csv.reader(stream)

            # Get and validate header row
            try:
                header_row = next(csv_input)
                print(f"CSV Header: {header_row}")
            except StopIteration:
                return jsonify({'error': 'CSV file is empty'}), 400

            voters_added = 0
            voters_skipped = 0
            invalid_rows = 0
            errors = []

            for row_num, row in enumerate(csv_input, start=2):
                try:
                    print(f"Processing row {row_num}: {row}")

                    # Support both 3-column (without voting token) and 4-column (with voting token) format
                    if len(row) >= 3:
                        member_id = row[0].strip() if len(row) > 0 else ""
                        full_name = row[1].strip() if len(row) > 1 else ""
                        phone_number = row[2].strip() if len(row) > 2 else ""

                        # Validate required data
                        if not member_id or not full_name or not phone_number:
                            error_msg = f"Row {row_num}: Missing required data (MemberID, FullName, or Phone)"
                            errors.append(error_msg)
                            print(error_msg)
                            invalid_rows += 1
                            continue

                        # Basic phone number validation (should contain digits)
                        if not any(char.isdigit() for char in phone_number):
                            error_msg = f"Row {row_num}: Invalid phone number (no digits): {phone_number}"
                            errors.append(error_msg)
                            print(error_msg)
                            invalid_rows += 1
                            continue

                        # Check if voter already exists - with better error handling
                        try:
                            existing_voter = Voter.query.filter_by(member_id=member_id).first()
                            if existing_voter:
                                print(f"Row {row_num}: Skipping duplicate member ID: {member_id}")
                                voters_skipped += 1
                                continue
                        except Exception as db_error:
                            error_msg = f"Row {row_num}: Database error checking voter {member_id}: {db_error}"
                            errors.append(error_msg)
                            print(error_msg)
                            invalid_rows += 1
                            continue

                        # Generate voting token automatically if not provided in CSV
                        voting_token = None
                        if len(row) >= 4 and row[3].strip():
                            # Use provided voting token if valid
                            provided_token = row[3].strip()
                            if provided_token.isdigit() and len(provided_token) == 8:
                                voting_token = provided_token
                            else:
                                error_msg = f"Row {row_num}: Invalid voting token format for {member_id}, generating new one"
                                errors.append(error_msg)
                                print(error_msg)
                                voting_token = None

                        try:
                            # Create voter object first to validate data
                            voter_data = {
                                'member_id': member_id,
                                'full_name': full_name,
                                'phone_number': phone_number,
                                'voting_token': voting_token
                            }

                            # Test if we can create the voter object
                            test_voter = Voter(**voter_data)
                            test_voter.generate_voter_id()
                            if not test_voter.voting_token:
                                test_voter.generate_voting_token()

                            # If we get here, the voter object is valid, so add to session
                            db.session.add(test_voter)
                            voters_added += 1
                            print(f"Row {row_num}: Added voter: {member_id} - {full_name}")

                        except Exception as voter_error:
                            error_msg = f"Row {row_num}: Error creating voter {member_id}: {voter_error}"
                            errors.append(error_msg)
                            print(error_msg)
                            invalid_rows += 1
                            continue

                except Exception as row_error:
                    error_msg = f"Row {row_num}: Error processing row: {row_error}"
                    errors.append(error_msg)
                    print(error_msg)
                    invalid_rows += 1
                    continue

            # Commit all changes - with comprehensive error handling
            if voters_added > 0:
                try:
                    db.session.commit()
                    print(f"Upload completed: {voters_added} added, {voters_skipped} skipped, {invalid_rows} invalid")
                except Exception as commit_error:
                    db.session.rollback()
                    print(f"Database commit error: {commit_error}")
                    import traceback
                    traceback.print_exc()
                    return jsonify({'error': f'Database error during save: {str(commit_error)}'}), 500
            else:
                print(f"No voters to commit: {voters_added} added, {voters_skipped} skipped, {invalid_rows} invalid")

            message = f'{voters_added} voters uploaded successfully with Voter IDs generated'
            if voters_skipped > 0:
                message += f' ({voters_skipped} duplicates skipped)'
            if invalid_rows > 0:
                message += f' ({invalid_rows} invalid rows skipped)'

            response_data = {
                'message': message,
                'added': voters_added,
                'skipped': voters_skipped,
                'invalid': invalid_rows
            }

            if errors:
                response_data['errors'] = errors[:10]  # Limit to first 10 errors

            return jsonify(response_data), 200

        except UnicodeDecodeError:
            return jsonify({'error': 'File encoding error. Please save your CSV file as UTF-8.'}), 400
        except Exception as csv_error:
            print(f"CSV processing error: {csv_error}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Error processing CSV file: {str(csv_error)}'}), 400

    except Exception as e:
        print(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
        # Always return JSON, never let an unhandled exception through
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@admin.route('/generate-ids', methods=['POST'])
def generate_voter_ids():
    if not request.headers.get('Authorization') == 'Bearer ' + os.environ.get('ADMIN_TOKEN', 'admin-token'):
        return jsonify({'error': 'Unauthorized'}), 401

    voters = Voter.query.filter_by(voter_id=None).all()
    ids_generated = 0

    for voter in voters:
        voter.generate_voter_id()
        ids_generated += 1

    db.session.commit()
    return jsonify({'message': f'Voter IDs generated for {ids_generated} voters'}), 200


@admin.route('/export-results')
def export_results():
    if not request.headers.get('Authorization') == 'Bearer ' + os.environ.get('ADMIN_TOKEN', 'admin-token'):
        return jsonify({'error': 'Unauthorized'}), 401

    # Get positions that have voting enabled and have candidates
    all_positions = Position.query.all()
    positions = [pos for pos in all_positions if pos.voting_enabled and pos.candidates]

    # Create CSV content
    import io
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Position', 'Candidate', 'Votes'])

    # Write data
    for position in positions:
        position_candidates = Candidate.query.filter_by(position_id=position.id).all()
        for candidate in position_candidates:
            writer.writerow([
                position.name,
                candidate.name,
                len(candidate.votes)
            ])

    # Get CSV content
    csv_content = output.getvalue()
    output.close()

    # Create response with CSV file
    from flask import Response
    response = Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-disposition': 'attachment; filename=slgs_obu_election_results.csv'
        }
    )

    return response

@admin.route('/clear-voters', methods=['POST'])
def clear_voters():
    if not request.headers.get('Authorization') == 'Bearer ' + os.environ.get('ADMIN_TOKEN', 'admin-token'):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Clear all voters
        voters_cleared = db.session.query(Voter).count()
        db.session.query(Voter).delete()
        db.session.commit()
        return jsonify({'message': f'All {voters_cleared} voters cleared successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Candidate management endpoints (admin-only)
def _is_admin_req(req):
    return req.headers.get('Authorization') == 'Bearer ' + os.environ.get('ADMIN_TOKEN', 'admin-token')


@admin.route('/candidates', methods=['GET'])
def list_candidates():
    if not _is_admin_req(request):
        return jsonify({'error': 'Unauthorized'}), 401
    candidates = Candidate.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'bio': c.bio,
        'photo_url': c.photo_url,
        'position_id': c.position_id
    } for c in candidates])


@admin.route('/candidates', methods=['POST'])
def create_candidate():
    if not _is_admin_req(request):
        return jsonify({'error': 'Unauthorized'}), 401
    # Support JSON or multipart/form-data with optional file upload
    try:
        name = None
        bio = None
        position_id = None
        photo_url = None

        if request.content_type and 'multipart/form-data' in request.content_type:
            name = request.form.get('name')
            bio = request.form.get('bio')
            position_id = request.form.get('position_id')
            try:
                position_id = int(position_id) if position_id is not None else None
            except Exception:
                # leave as-is; validation later
                pass

            file = request.files.get('photo_file')
            if file and file.filename:
                upload_dir = os.path.join(current_app.instance_path, 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_dir, filename)
                # Avoid clobbering existing files - prefix with timestamp if exists
                if os.path.exists(filepath):
                    import time
                    filename = f"{int(time.time())}_{filename}"
                    filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                # Serve via /uploads/<filename>
                photo_url = url_for('main.uploaded_file', filename=filename)
        else:
            data = request.get_json() or {}
            name = data.get('name')
            bio = data.get('bio')
            position_id = data.get('position_id')
            photo_url = data.get('photo_url')

        if not name or not position_id:
            return jsonify({'error': 'name and position_id required'}), 400

        cand = Candidate(name=name, bio=bio, photo_url=photo_url, position_id=position_id)
        db.session.add(cand)
        db.session.commit()
        return jsonify({'message': 'Candidate created', 'id': cand.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin.route('/candidates/<int:candidate_id>', methods=['PUT'])
def update_candidate(candidate_id):
    if not _is_admin_req(request):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        cand = Candidate.query.get(candidate_id)
        if not cand:
            return jsonify({'error': 'Not found'}), 404

        if request.content_type and 'multipart/form-data' in request.content_type:
            name = request.form.get('name')
            bio = request.form.get('bio')
            position_id = request.form.get('position_id')
            try:
                position_id = int(position_id) if position_id is not None and position_id != '' else None
            except Exception:
                pass
            file = request.files.get('photo_file')

            if name:
                cand.name = name
            if bio is not None:
                cand.bio = bio
            if position_id:
                cand.position_id = position_id
            if file and file.filename:
                upload_dir = os.path.join(current_app.instance_path, 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_dir, filename)
                if os.path.exists(filepath):
                    import time
                    filename = f"{int(time.time())}_{filename}"
                    filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                cand.photo_url = url_for('main.uploaded_file', filename=filename)
        else:
            data = request.get_json() or {}
            cand.name = data.get('name', cand.name)
            cand.bio = data.get('bio', cand.bio)
            cand.photo_url = data.get('photo_url', cand.photo_url)
            cand.position_id = data.get('position_id', cand.position_id)

        db.session.commit()
        return jsonify({'message': 'Candidate updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin.route('/candidates/<int:candidate_id>', methods=['DELETE'])
def delete_candidate(candidate_id):
    if not _is_admin_req(request):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        cand = Candidate.query.get(candidate_id)
        if not cand:
            return jsonify({'error': 'Not found'}), 404
        db.session.delete(cand)
        db.session.commit()
        return jsonify({'message': 'Candidate deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin.route('/positions', methods=['GET'])
def list_positions():
    if not _is_admin_req(request):
        return jsonify({'error': 'Unauthorized'}), 401
    positions = Position.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'voting_enabled': p.voting_enabled,
        'candidate_count': len(p.candidates)
    } for p in positions])


@admin.route('/positions/<int:position_id>/toggle-voting', methods=['POST'])
def toggle_position_voting(position_id):
    """Toggle voting status for a specific position"""
    if not _is_admin_req(request):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        position = Position.query.get(position_id)
        if not position:
            return jsonify({'error': 'Position not found'}), 404

        # Toggle the voting status
        position.voting_enabled = not position.voting_enabled
        db.session.commit()

        return jsonify({
            'message': f'Voting {"enabled" if position.voting_enabled else "disabled"} for {position.name}',
            'position_id': position.id,
            'name': position.name,
            'voting_enabled': position.voting_enabled
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin.route('/create-positions', methods=['POST'])
def create_positions():
    """Force create SLGS OBU positions if they don't exist"""
    if not _is_admin_req(request):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Create all 12 positions for the General Election
        positions_data = [
            ('President', True), ('Vice President', True), ('Secretary', True),
            ('Assistant Secretary', False), ('Treasurer', False), ('Assistant Treasurer', False),
            ('Social & Organizing Secretary', False), ('Assistant Social Secretary & Organizing Secretary', False),
            ('Publicity Secretary', False), ('Chairman Improvement Committee', False),
            ('Diaspora Coordinator', False), ('Chief Whip', False)
        ]

        created_count = 0
        existing_count = 0

        for name, voting_enabled in positions_data:
            existing = Position.query.filter_by(name=name).first()
            if not existing:
                pos = Position(
                    name=name,
                    description=f'{name} of SLGS Old Boys Union',
                    voting_enabled=voting_enabled
                )
                db.session.add(pos)
                created_count += 1
                print(f'Created position: {name} (voting: {voting_enabled})')
            else:
                # Update existing position's voting status
                if existing.voting_enabled != voting_enabled:
                    existing.voting_enabled = voting_enabled
                    print(f'Updated position: {name} (voting: {voting_enabled})')
                existing_count += 1
                print(f'Position already exists: {name}')

        if created_count > 0:
            db.session.commit()
            print(f'Committed {created_count} new positions to database')

        # Return detailed status
        return jsonify({
            'message': f'Created {created_count} positions, {existing_count} already existed',
            'created': created_count,
            'existing': existing_count,
            'total_positions': len(positions_data)
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f'Error creating positions: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@admin.route('/check-positions', methods=['GET'])
def check_positions():
    """Debug endpoint to check current positions in database"""
    if not _is_admin_req(request):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        positions = Position.query.all()
        positions_list = [{'id': p.id, 'name': p.name, 'description': p.description} for p in positions]

        return jsonify({
            'count': len(positions_list),
            'positions': positions_list
        }), 200

    except Exception as e:
        return jsonify({'error': str(e), 'count': 0, 'positions': []}), 500


@admin.route('/fix-database', methods=['POST'])
def fix_database():
    """Fix database schema issues (adds missing columns and updates sizes)"""
    if not _is_admin_req(request):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Check if we're using PostgreSQL
        if not current_app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
            return jsonify({'error': 'This fix is only for PostgreSQL databases'}), 400

        with db.engine.connect() as conn:
            try:
                # First, clear any failed transactions
                conn.execute(db.text("ROLLBACK"))
                print("Rolled back any existing failed transactions")

                fixes_applied = []

                # Fix 1: Update voter_id column size from VARCHAR(8) to VARCHAR(20)
                try:
                    # Check current voter_id column size
                    result = conn.execute(db.text("""
                        SELECT character_maximum_length
                        FROM information_schema.columns
                        WHERE table_name = 'voter' AND column_name = 'voter_id'
                    """))
                    current_size = result.scalar()

                    if current_size == 8:
                        print(f"Current voter_id column size: {current_size}, updating to 20")
                        conn.execute(db.text("ALTER TABLE voter ALTER COLUMN voter_id TYPE VARCHAR(20)"))
                        fixes_applied.append("Updated voter_id column from VARCHAR(8) to VARCHAR(20)")
                        print("✅ Successfully updated voter_id column size")
                    else:
                        print(f"voter_id column already has size: {current_size}")

                except Exception as e:
                    print(f"Error updating voter_id column: {e}")
                    return jsonify({'error': f'Failed to update voter_id column: {str(e)}'}), 500

                # Fix 2: Ensure voting_token column exists
                try:
                    result = conn.execute(db.text("SELECT voting_token FROM voter LIMIT 1"))
                    print("✅ voting_token column already exists")
                except Exception:
                    # Column doesn't exist, add it
                    try:
                        conn.execute(db.text("ALTER TABLE voter ADD COLUMN voting_token VARCHAR(8) UNIQUE"))
                        fixes_applied.append("Added voting_token column")
                        print("✅ Successfully added voting_token column")
                    except Exception as e:
                        return jsonify({'error': f'Failed to add voting_token column: {str(e)}'}), 500

                conn.commit()

                # Verify fixes
                try:
                    result = conn.execute(db.text("""
                        SELECT column_name, character_maximum_length
                        FROM information_schema.columns
                        WHERE table_name = 'voter' AND column_name IN ('voter_id', 'voting_token')
                    """))

                    column_info = {row[0]: row[1] for row in result}
                    verification = []
                    verification.append(f"voter_id column size: {column_info.get('voter_id', 'unknown')}")
                    verification.append(f"voting_token column size: {column_info.get('voting_token', 'unknown')}")

                except Exception as e:
                    verification = [f"Error verifying columns: {str(e)}"]

                return jsonify({
                    'message': f'✅ Database fixes applied successfully: {", ".join(fixes_applied)}',
                    'verification': verification,
                    'fixes_count': len(fixes_applied)
                }), 200

            except Exception as alter_error:
                # Try to rollback and retry once
                try:
                    conn.execute(db.text("ROLLBACK"))
                    print("Retrying after rollback...")

                    # Just update the voter_id column size
                    conn.execute(db.text("ALTER TABLE voter ALTER COLUMN voter_id TYPE VARCHAR(20)"))
                    conn.commit()

                    return jsonify({
                        'message': '✅ Successfully updated voter_id column size (after retry)',
                        'fixes_count': 1
                    }), 200

                except Exception as retry_error:
                    return jsonify({'error': f'Failed to fix database after retry: {str(retry_error)}'}), 500

    except Exception as e:
        return jsonify({'error': f'Database fix error: {str(e)}'}), 500


@admin.route('/clear-all-data', methods=['POST'])
def clear_all_data():
    """Clear all voters and reset the system"""
    if not _is_admin_req(request):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # Clear votes first (due to foreign key constraints)
        votes_cleared = Vote.query.count()
        Vote.query.delete()

        # Clear all candidates
        candidates_cleared = Candidate.query.count()
        Candidate.query.delete()

        # Clear all voters (now that votes are cleared)
        voters_cleared = Voter.query.count()
        Voter.query.delete()

        # Reset voting status
        voting_setting = Setting.query.filter_by(key='voting_open').first()
        if voting_setting:
            voting_setting.value = 'false'

        until_setting = Setting.query.filter_by(key='voting_until').first()
        if until_setting:
            db.session.delete(until_setting)

        db.session.commit()

        return jsonify({
            'message': f'System reset successful: {voters_cleared} voters, {votes_cleared} votes, and {candidates_cleared} candidates cleared'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

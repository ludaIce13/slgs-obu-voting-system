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

        # Validate Voter ID format (must be exactly 8 digits)
        if not (voter_id.isdigit() and len(voter_id) == 8):
            print(f"VOTE REJECTED - Invalid Voter ID format: {voter_id}")
            flash('Voter ID must be exactly 8 digits.', 'error')
            return redirect(url_for('main.vote'))

        # Validate Voting Token format (must be exactly 16 alphanumeric characters)
        if not (voting_token.isalnum() and len(voting_token) == 16):
            print(f"VOTE REJECTED - Invalid Voting Token format: {voting_token}")
            flash('Voting Token must be exactly 16 alphanumeric characters.', 'error')
            return redirect(url_for('main.vote'))

        # Find voter by both Voter ID and Voting Token
        voter = Voter.query.filter_by(voter_id=voter_id, voting_token=voting_token).first()
        print(f"VOTE VALIDATION - Voter found: {voter is not None}")

        if not voter:
            print(f"VOTE REJECTED - Voter ID/Token combination not found: {voter_id}")
            flash('Invalid Voter ID or Voting Token combination.', 'error')
            return redirect(url_for('main.vote'))

        if voter.has_voted:
            print(f"VOTE REJECTED - Voter already voted: {voter_id}")
            flash('This Voter ID has already been used.', 'error')
            return redirect(url_for('main.vote'))

        # Get votes for all positions
        positions = Position.query.all()
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

        if votes_recorded == 0:
            flash('Please select at least one candidate.', 'error')
            return redirect(url_for('main.vote'))

        # Mark voter as voted
        voter.has_voted = True
        db.session.commit()

        print(f"VOTE SUCCESS - Voter {voter.full_name} ({voter_id}) voted successfully")
        flash('Your votes have been recorded successfully!', 'success')
        return redirect(url_for('main.thank_you'))

    try:
        positions = Position.query.all()
        print(f"Vote page loaded - Found {len(positions)} positions")
        return render_template('vote.html', positions=positions)
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
                    positions_data = [
                        'President', 'Vice President', 'Secretary', 'Assistant Secretary',
                        'Treasurer', 'Assistant Treasurer', 'Social & Organizing Secretary',
                        'Assistant Social Secretary & Organizing Secretary', 'Publicity Secretary',
                        'Chairman Improvement Committee', 'Diaspora Coordinator', 'Chief Whip'
                    ]

                    for name in positions_data:
                        pos = Position(name=name, description=f'{name} of SLGS Old Boys Union')
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
    if not request.headers.get('Authorization') == 'Bearer ' + os.environ.get('ADMIN_TOKEN', 'admin-token'):
        return jsonify({'error': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and file.filename.endswith('.csv'):
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)

        next(csv_input)  # Skip header row

        voters_added = 0
        voters_skipped = 0
        invalid_rows = 0

        for row in csv_input:
            if len(row) >= 4:
                member_id, full_name, phone_number, voting_token = row[:4]

                # Validate data
                if not member_id or not full_name or not phone_number or not voting_token:
                    invalid_rows += 1
                    continue

                # Basic phone number validation (should contain digits)
                if not any(char.isdigit() for char in phone_number):
                    invalid_rows += 1
                    continue

                # Voting token validation (should be 16 alphanumeric characters)
                if not (voting_token.isalnum() and len(voting_token) == 16):
                    invalid_rows += 1
                    continue

                # Check if voter already exists
                existing_voter = Voter.query.filter_by(member_id=member_id).first()
                if existing_voter:
                    # Skip duplicate member ID
                    voters_skipped += 1
                    continue

                # Check if voting token already exists
                existing_token = Voter.query.filter_by(voting_token=voting_token).first()
                if existing_token:
                    invalid_rows += 1
                    continue

                voter = Voter(
                    member_id=member_id,
                    full_name=full_name,
                    phone_number=phone_number.strip(),
                    voting_token=voting_token.strip()
                )
                voter.generate_voter_id()
                db.session.add(voter)
                voters_added += 1

        db.session.commit()

        message = f'{voters_added} voters uploaded successfully with Voter IDs generated'
        if voters_skipped > 0:
            message += f' ({voters_skipped} duplicates skipped)'
        if invalid_rows > 0:
            message += f' ({invalid_rows} invalid rows skipped)'

        return jsonify({'message': message}), 200

    return jsonify({'error': 'Invalid file format'}), 400

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

    positions = Position.query.all()

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
                position_id = int(position_id) if position_id is not None else None
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
        return jsonify({'message': 'Candidate updated'})
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
    return jsonify([{'id': p.id, 'name': p.name} for p in positions])


@admin.route('/create-positions', methods=['POST'])
def create_positions():
    """Force create SLGS OBU positions if they don't exist"""
    if not _is_admin_req(request):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        positions_data = [
            'President', 'Vice President', 'Secretary', 'Assistant Secretary',
            'Treasurer', 'Assistant Treasurer', 'Social & Organizing Secretary',
            'Assistant Social Secretary & Organizing Secretary', 'Publicity Secretary',
            'Chairman Improvement Committee', 'Diaspora Coordinator', 'Chief Whip'
        ]

        created_count = 0
        for name in positions_data:
            existing = Position.query.filter_by(name=name).first()
            if not existing:
                pos = Position(name=name, description=f'{name} of SLGS Old Boys Union')
                db.session.add(pos)
                created_count += 1

        if created_count > 0:
            db.session.commit()
            return jsonify({'message': f'Created {created_count} positions successfully'}), 200
        else:
            return jsonify({'message': f'All {len(positions_data)} positions already exist'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# SLGS OBU Voting System

A secure, web-based voting system for the Sierra Leone Grammar School Old Boys Union (SLGS OBU) presidential and officer elections. This system supports voting for all 12 official positions with unique Voter ID authentication.

## Features

- **No Email Required**: Voters use unique 8-digit numeric Voter IDs
- **Multi-Position Voting**: Vote for all 12 positions (President, VP, Secretary, etc.) with one ID
- **Anonymous Voting**: No linkage between voter identity and vote choices
- **Real-time Dashboard**: Live vote counts and turnout monitoring
- **Admin Management**: Upload voter lists, generate IDs, export results
- **Duplicate Prevention**: Each Voter ID can only be used once
- **Secure Authentication**: Admin token-based access control

## Supported Positions

1. **President** - 3 candidates
2. **Vice President** - 2 candidates
3. **Secretary** - 2 candidates
4. **Assistant Secretary** - 2 candidates
5. **Treasurer** - 2 candidates
6. **Assistant Treasurer** - 2 candidates
7. **Social & Organizing Secretary** - 2 candidates
8. **Assistant Social Secretary & Organizing Secretary** - 2 candidates
9. **Publicity Secretary** - 2 candidates
10. **Chairman Improvement Committee** - 2 candidates
11. **Diaspora Coordinator** - 2 candidates
12. **Chief Whip** - 2 candidates

## Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Setup sample data (positions and candidates)
python setup_sample_data.py

# Run the application
python run.py
```

### 2. Access the System

- **Voting Page**: http://localhost:5000/vote
- **Admin Dashboard**: http://localhost:5000/admin
- **Admin Token**: `admin-token` (default)

### 3. Admin Setup

1. Go to http://localhost:5000/admin
2. Enter admin token: `admin-token`
3. Upload voter CSV file with format: `MemberID,FullName,GraduationYear`
4. Generate Voter IDs for all uploaded voters
5. Distribute Voter IDs to voters (print, WhatsApp, etc.)

### 4. Voting Process

1. Voters go to http://localhost:5000/vote
2. Enter their 8-digit Voter ID
3. Select candidates for each position
4. Submit votes (ID becomes invalid after use)

## CSV Voter File Format

Create a CSV file with the following columns:

```csv
MemberID,FullName,GraduationYear
SLGS001,John Doe,1995
SLGS002,Jane Smith,1996
SLGS003,Bob Johnson,1997
```

- **MemberID**: Unique identifier (e.g., SLGS001, SLGS002)
- **FullName**: Voter's full name
- **GraduationYear**: Year of graduation (numeric)

## Admin Functions

### Upload Voters
- Upload CSV file with voter data
- System automatically generates unique 8-digit Voter IDs
- Handles duplicates gracefully (skips existing MemberIDs)

### Generate Voter IDs
- Generates IDs for voters without existing IDs
- 8-digit numeric format (e.g., 73948201)

### Export Results
- Exports vote counts for all positions and candidates
- Available as JSON data (can be extended to CSV/PDF)

### Clear All Voters
- **DANGER**: Permanently deletes all voter data
- Use with caution - cannot be undone

### View Voter Status
- See all voters with their IDs and voting status
- Track who has voted and who hasn't

## Security Features

- **No Personal Data Storage**: Only anonymized vote tallies stored
- **Single-Use IDs**: Each Voter ID can only be used once
- **Admin Token Authentication**: Token-based admin access
- **HTTPS Ready**: Configure for production HTTPS deployment

## Configuration

### Environment Variables

Create a `.env` file:

```env
ADMIN_TOKEN=your-secure-admin-token
FLASK_ENV=development
```

### Admin Token

- Default: `admin-token`
- Change via `ADMIN_TOKEN` environment variable
- Stored in browser localStorage for session persistence

## Deployment

### Local Development

```bash
python run.py
```

### Production Deployment

1. Set `ADMIN_TOKEN` environment variable
2. Use a WSGI server like Gunicorn
3. Configure HTTPS
4. Set up reverse proxy (nginx)

Example with Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## File Structure

```
slgs-voting-system/
├── app/
│   ├── __init__.py      # Flask app factory
│   ├── models.py        # Database models
│   └── routes.py        # Route handlers
├── templates/           # HTML templates
├── static/             # CSS/JS files
├── data/               # Sample data
├── instance/           # SQLite database
├── requirements.txt    # Python dependencies
├── run.py             # Application entry point
└── setup_sample_data.py # Sample data generator
```

## Database Schema

### Voter Model
- `member_id`: Unique member identifier
- `full_name`: Voter's full name
- `graduation_year`: Year of graduation
- `voter_id`: 8-digit unique voting ID
- `has_voted`: Boolean voting status

### Position Model
- `name`: Position name (e.g., "President")
- `description`: Optional description

### Candidate Model
- `name`: Candidate name
- `position_id`: Foreign key to position

### Vote Model
- `voter_id`: Foreign key to voter
- `candidate_id`: Foreign key to candidate
- `position_id`: Foreign key to position
- `ip_address`: Voter's IP address
- `user_agent`: Browser user agent

## API Endpoints

### Public Endpoints
- `GET /` - Home page
- `GET/POST /vote` - Voting interface
- `GET /thank-you` - Post-vote confirmation

### Admin Endpoints
- `GET /admin` - Admin dashboard
- `POST /admin/upload-voters` - Upload voter CSV
- `POST /admin/generate-ids` - Generate voter IDs
- `GET /admin/export-results` - Export vote results
- `POST /admin/clear-voters` - Clear all voter data

## Troubleshooting

### Common Issues

1. **"Invalid Voter ID"**
   - Check if Voter ID exists in database
   - Verify ID format (8 digits)

2. **"This ID has already been used"**
   - Voter ID has already been used to vote
   - Each ID can only be used once

3. **Admin Authorization Error**
   - Check admin token in environment variable
   - Verify token in browser localStorage

4. **Database Errors**
   - Run `python setup_sample_data.py` to recreate database
   - Check file permissions on `instance/voting.db`

### Debug Mode

Enable debug mode by setting:

```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## Support

For technical support or questions about the SLGS OBU Voting System, please contact the development team.

---

**Sierra Leone Grammar School Old Boys Union (SLGS OBU)**  
*Secure • Anonymous • Reliable Voting System*
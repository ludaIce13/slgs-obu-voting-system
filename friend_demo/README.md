# Universal Voting System

A secure, configurable web-based voting system that can be customized for any organization's elections. Originally built for the Sierra Leone Grammar School Old Boys Union (SLGS OBU), this system can be easily adapted for any organization.

## Configuration

This voting system is fully configurable via environment variables. You can customize:

- **Organization Name**: Set your organization's name
- **Election Title**: Define the election type (e.g., "General Election", "Board Election", etc.)
- **Positions**: Configure the specific positions being voted on
- **Admin Token**: Set a custom admin password

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Organization Configuration
ORGANIZATION_NAME="Your Organization Name"
ELECTION_TITLE="Your Election Title"

# Admin Configuration
ADMIN_TOKEN="your-secure-admin-token"

# Optional: Custom Positions (comma-separated)
ELECTION_POSITIONS="President,Vice President,Secretary,Treasurer,Chairperson"
```

### Default Configuration (SLGS OBU)

If no environment variables are set, the system defaults to:

- **Organization**: SLGS Old Boys Union
- **Election**: General Election
- **Positions**: President, Vice President, Secretary, Assistant Secretary, Treasurer, Assistant Treasurer, Social & Organizing Secretary, Assistant Social Secretary & Organizing Secretary, Publicity Secretary, Chairman Improvement Committee, Diaspora Coordinator, Chief Whip
- **Admin Token**: admin-token

## Quick Start for New Organizations

1. **Clone the repository**
2. **Set environment variables** in `.env` file
3. **Deploy to Render** (or your preferred platform)
4. **Upload your voter list** via the admin panel
5. **Configure positions** if different from defaults
6. **Start the election!**

## Features

- ✅ **Secure Authentication**: Dual-factor authentication with Voter ID and 8-digit tokens
- ✅ **Anonymous Voting**: No linkage between voters and their choices
- ✅ **Real-time Dashboard**: Live results display during elections
- ✅ **Admin Panel**: Full election management and monitoring
- ✅ **CSV Import**: Easy voter list management
- ✅ **Mobile Friendly**: Responsive design for all devices
- ✅ **Production Ready**: Built for high-traffic elections
- ✅ **Fully Configurable**: Customize organization, positions, and branding

## Supported Positions (Configurable)

The system supports any number of positions. Default configuration includes:

1. **President** - Leadership position
2. **Vice President** - Deputy leadership
3. **Secretary** - Administrative role
4. **Assistant Secretary** - Administrative support
5. **Treasurer** - Financial management
6. **Assistant Treasurer** - Financial support
7. **Social & Organizing Secretary** - Event coordination
8. **Assistant Social Secretary & Organizing Secretary** - Event support
9. **Publicity Secretary** - Communications
10. **Chairman Improvement Committee** - Quality improvement
11. **Diaspora Coordinator** - International relations
12. **Chief Whip** - Party discipline

**Note**: Positions can be customized via the `ELECTION_POSITIONS` environment variable.

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
- **Public Dashboard**: http://localhost:5000/dashboard
- **Admin Token**: `admin-token` (default - change via environment variable)

### 3. Admin Setup

1. Go to http://localhost:5000/admin
2. Enter admin token (set via `ADMIN_TOKEN` environment variable)
3. Upload voter CSV file with format: `MemberID,FullName,PhoneNumber,VotingToken` (optional)
4. Generate Voter IDs for all uploaded voters
5. Distribute Voter IDs and tokens to voters

### 4. Voting Process

1. Voters go to http://localhost:5000/vote
2. Enter their Voter ID and 8-digit Voting Token
3. Select candidates for each position
4. Submit votes (credentials become invalid after use)

## CSV Voter File Format

Create a CSV file with the following columns:

```csv
MemberID,FullName,PhoneNumber,VotingToken
ORG001,John Doe,+1234567890,12345678
ORG002,Jane Smith,+1234567891,
ORG003,Bob Johnson,+1234567892,87654321
```

- **MemberID**: Unique identifier (e.g., ORG001, ORG002)
- **FullName**: Voter's full name
- **PhoneNumber**: Contact phone number
- **VotingToken**: Optional 8-digit token (leave blank to auto-generate)

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

Create a `.env` file in the project root:

```env
# Organization Configuration
ORGANIZATION_NAME="Your Organization Name"
ELECTION_TITLE="Your Election Title"

# Admin Configuration
ADMIN_TOKEN="your-secure-admin-token"

# Optional: Custom Positions (comma-separated)
ELECTION_POSITIONS="President,Vice President,Secretary,Treasurer,Chairperson"

# Development
FLASK_ENV=development
```

### Organization Configuration

- **ORGANIZATION_NAME**: Your organization's full name (default: "SLGS Old Boys Union")
- **ELECTION_TITLE**: Type of election (default: "General Election")
- **ELECTION_POSITIONS**: Comma-separated list of positions (optional)

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

The system is optimized for cloud platforms like Render, Railway, or Heroku.

#### Render Deployment

1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard:
   - `ADMIN_TOKEN`: Your secure admin password
   - `ORGANIZATION_NAME`: Your organization name
   - `ELECTION_TITLE`: Your election title
   - `ELECTION_POSITIONS`: Comma-separated positions (optional)
3. Deploy automatically

#### Environment Variables for Production

```bash
# Required
ADMIN_TOKEN=your-secure-admin-token-here

# Organization (customize these)
ORGANIZATION_NAME=Your Organization Name
ELECTION_TITLE=Your Election Title

# Optional
ELECTION_POSITIONS=Position1,Position2,Position3
DATABASE_URL=postgresql://... (if using PostgreSQL)
```

#### Manual Deployment with Gunicorn

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

## Example Configurations

### For a University Student Council Election

```bash
ORGANIZATION_NAME="University of Example Student Council"
ELECTION_TITLE="Annual Elections"
ELECTION_POSITIONS="President,Vice President,Secretary,Treasurer,Social Chair,Academic Chair,Sports Chair"
ADMIN_TOKEN="student-council-2024"
```

### For a Professional Association Board Election

```bash
ORGANIZATION_NAME="Professional Engineers Association"
ELECTION_TITLE="Board of Directors Election"
ELECTION_POSITIONS="Chair,Vice Chair,Secretary,Treasurer,Director,Education Chair,Membership Chair"
ADMIN_TOKEN="pea-board-2024"
```

### For a Community Organization Election

```bash
ORGANIZATION_NAME="Downtown Community Center"
ELECTION_TITLE="Board Election"
ELECTION_POSITIONS="President,Vice President,Secretary,Treasurer,Program Director,Volunteer Coordinator"
ADMIN_TOKEN="dcc-board-2024"
```

## Support

For technical support or customization requests, please contact the development team.

---

**Universal Voting System**
*Secure • Anonymous • Configurable • Production-Ready*
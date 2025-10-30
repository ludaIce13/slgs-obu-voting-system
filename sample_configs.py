#!/usr/bin/env python3
"""
Sample configurations for different organization types
Run this to see example deployment commands for various organizations
"""

import os

def print_sample_configs():
    """Print sample configurations for different organization types"""

    configs = [
        {
            "name": "Tech Professionals Association",
            "election": "Board of Directors Election",
            "positions": "President,Vice President,Secretary,Treasurer,Program Chair,Education Chair,Membership Chair",
            "token": "tpa-board-2024"
        },
        {
            "name": "University Student Council",
            "election": "Annual Elections",
            "positions": "President,Vice President,Secretary,Treasurer,Social Chair,Academic Chair,Sports Chair",
            "token": "usc-elections-2024"
        },
        {
            "name": "Professional Engineers Association",
            "election": "Board of Directors Election",
            "positions": "Chair,Vice Chair,Secretary,Treasurer,Director,Education Chair,Membership Chair",
            "token": "pea-board-2024"
        },
        {
            "name": "Downtown Community Center",
            "election": "Board Election",
            "positions": "President,Vice President,Secretary,Treasurer,Program Director,Volunteer Coordinator",
            "token": "dcc-board-2024"
        },
        {
            "name": "Medical Association",
            "election": "Executive Committee Election",
            "positions": "President,Vice President,Secretary,Treasurer,Ethics Chair,Education Chair,Communications Chair",
            "token": "med-assoc-2024"
        },
        {
            "name": "Environmental NGO",
            "election": "Board of Trustees Election",
            "positions": "Chair,Vice Chair,Secretary,Treasurer,Program Director,Development Director,Policy Director",
            "token": "env-ngo-2024"
        }
    ]

    print("Universal Voting System - Sample Configurations")
    print("=" * 60)
    print()

    for i, config in enumerate(configs, 1):
        print(f"{i}. {config['name']}")
        print(f"   Election: {config['election']}")
        print(f"   Positions: {len(config['positions'].split(','))} positions")
        print(f"   Admin Token: {config['token']}")
        print()
        print("   Deployment Command:")
        print(f"   python deploy.py \\")
        print(f"     --org \"{config['name']}\" \\")
        print(f"     --election \"{config['election']}\" \\")
        print(f"     --positions \"{config['positions']}\" \\")
        print(f"     --admin-token \"{config['token']}\" \\")
        print(f"     --output \"{config['name'].lower().replace(' ', '_')}_deployment\"")
        print()
        print("-" * 40)
        print()

def create_pricing_guide():
    """Create a pricing guide for clients"""

    pricing_content = """# Universal Voting System - Pricing Guide

## Service Packages

### Basic Package - $299
- Custom organization branding
- Up to 10 election positions
- Up to 500 voters
- 1 election deployment
- Email support during setup
- 30-day post-launch support

### Professional Package - $599
- Everything in Basic Package
- Unlimited election positions
- Up to 2,000 voters
- Multiple election deployments
- Phone/video call setup assistance
- 90-day post-launch support
- Custom domain setup help

### Enterprise Package - $999
- Everything in Professional Package
- Unlimited voters
- White-label solution
- Priority support
- Custom feature development (up to 5 hours)
- 6-month support package

## What's Included

### ✅ Core Features
- Secure, anonymous voting system
- Real-time results dashboard
- Admin management panel
- CSV voter import/export
- Mobile-responsive design
- Production deployment assistance

### ✅ Security & Compliance
- Dual-factor authentication
- One-time use voting tokens
- Anonymous vote storage
- Admin access controls
- HTTPS encryption
- Rate limiting protection

### ✅ Support & Training
- Step-by-step deployment guide
- Admin training session
- Voter setup assistance
- Technical support
- Documentation access

## Payment Terms

- 50% deposit required to begin customization
- 50% due upon successful deployment
- All packages include 30-day money-back guarantee
- Enterprise package includes custom development hours

## Add-on Services

- Custom domain setup: $50
- Additional training sessions: $100/hour
- Custom feature development: $150/hour
- Priority support: $200/month

## Ready to Get Started?

Contact us to discuss your election needs and get a custom quote!

**Email**: [your-email@example.com]
**Phone**: [your-phone-number]
"""

    with open('PRICING_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(pricing_content)

    print("Created PRICING_GUIDE.md")

def create_onboarding_guide():
    """Create a client onboarding guide"""

    onboarding_content = """# Client Onboarding Guide

## Welcome to Your Voting System!

This guide will walk you through the entire process from order to live election.

## Phase 1: Pre-Deployment (1-2 days)

### Step 1: Initial Consultation
- Discuss your election requirements
- Review position structure
- Determine voter list format
- Set timeline and deadlines

### Step 2: Configuration Setup
- Receive your custom deployment package
- Review environment variables
- Confirm admin token and credentials

### Step 3: Voter List Preparation
- Format your voter list as CSV
- Include required columns: MemberID, FullName, PhoneNumber, VotingToken
- Clean and validate data

## Phase 2: Deployment (1 day)

### Step 4: Platform Setup
- Choose deployment platform (Render/Railway/Heroku)
- Create account and connect repository
- Set environment variables
- Deploy application

### Step 5: System Testing
- Test admin login
- Upload sample voter data
- Test voting flow
- Verify dashboard functionality

## Phase 3: Election Setup (1-2 days)

### Step 6: Voter Data Upload
- Upload complete voter list
- Generate voting tokens
- Review voter statistics

### Step 7: Pre-Election Testing
- Send test credentials to administrators
- Test voting from different devices
- Verify results display correctly

### Step 8: Communication Plan
- Prepare voter instructions
- Set up support channels
- Create election timeline

## Phase 4: Election Day (Ongoing)

### Step 9: Election Monitoring
- Monitor voter turnout in real-time
- Track system performance
- Address any technical issues

### Step 10: Results Management
- Close voting when appropriate
- Export final results
- Prepare results announcement

## Phase 5: Post-Election (1 week)

### Step 11: Data Export
- Export complete voting records
- Generate audit reports
- Archive election data

### Step 12: System Decommission
- Securely delete voter data (if requested)
- Provide system access for future elections
- Schedule follow-up support

## Support Channels

### During Business Hours
- **Email**: [your-email@example.com]
- **Phone**: [your-phone-number]
- **Response Time**: Within 4 hours

### Emergency Support
- **Emergency Line**: [emergency-phone-number]
- **After Hours**: Email with "URGENT" in subject

## File Checklist

Before deployment, ensure you have:
- [ ] Custom .env file
- [ ] DEPLOYMENT_GUIDE.md
- [ ] Voter list CSV file
- [ ] Sample voters CSV
- [ ] README.md documentation

## Success Metrics

Your election will be successful when:
- ✅ All voters can access the voting page
- ✅ Admin panel shows correct voter counts
- ✅ Votes are recorded anonymously
- ✅ Results update in real-time
- ✅ No security breaches occur
- ✅ All stakeholders are satisfied

## Need Help?

Don't hesitate to reach out at any phase of the process. We're here to ensure your election runs smoothly and securely!
"""

    with open('CLIENT_ONBOARDING_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(onboarding_content)

    print("Created CLIENT_ONBOARDING_GUIDE.md")

if __name__ == '__main__':
    print_sample_configs()
    create_pricing_guide()
    create_onboarding_guide()
    print("\nSample configuration files created!")
    print("Run 'python deploy.py --help' to see deployment options.")
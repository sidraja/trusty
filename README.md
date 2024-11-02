# Trusty - AI Shopping Agent

Trusty is an AI-powered shopping agent that helps users make informed purchasing decisions by processing natural language requirements and managing transactions securely.

## Prerequisites

- Python 3.11+
- PostgreSQL
- OpenAI API key

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/trusty.git
   cd trusty
   ```

2. **Set up Python virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   ```bash
   createdb trusty
   ```

4. **Create .env file**
   Create a `.env` file in the project root with the following content:
   ```env
   DJANGO_ENV=localhost
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=postgres://postgres:postgres@localhost:5432/trusty
   DJANGO_LOG_LEVEL=INFO
   FE_BASE_URL=http://localhost:3000/

   # OpenAI settings
   OPENAI_API_KEY=your-openai-api-key-here
   OPENAI_MODEL=gpt-4
   MOCK_OPENAI_IN_TESTS=True

   # Security settings
   SECURE_SSL_REDIRECT=False
   SESSION_COOKIE_SECURE=False
   CSRF_COOKIE_SECURE=False
   ```

5. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

## Running the Application

1. **Start the Django development server**
   ```bash
   python manage.py runserver localhost:8000
   ```

2. **Run the test suite**
   ```bash
   # Run Django tests
   python manage.py test

   # Run external API tests
   python -m tests_external.api_tests.test_api_endpoints
   ```

## API Endpoints

- `POST /api/auth/register/` - Register a new user
- `POST /api/auth/token/` - Obtain JWT token
- `POST /api/agents/setup/` - Set up a new shopping agent
- `POST /api/agents/{id}/shop/` - Start shopping task
- `GET /api/agents/{id}/status/` - Get agent status
- `POST /api/transactions/verify/` - Verify transaction

## Development Notes

- The application uses OpenAI's GPT-4 for processing shopping requirements
- Default constraints are used when OpenAI processing fails
- Test mode uses mock data for OpenAI and blockchain interactions

## Troubleshooting

- If you see OpenAI API errors, check your API key and quota
- For database connection issues, verify PostgreSQL is running and credentials are correct
- Enable DEBUG=True in .env for detailed error messages

## Contributing

1. Create a feature branch
2. Make your changes
3. Run the test suite
4. Submit a pull request

## Legal Notice

This software is proprietary and confidential. All rights reserved. 
See the LICENSE file for full license details.

## Security

See SECURITY.md for reporting security vulnerabilities.

## Contributing

This is a private repository. External contributions are not accepted at this time.

## License

Copyright (c) 2024 All Rights Reserved

This software and associated documentation files (the "Software") are proprietary and confidential. 
All rights are reserved. No part of this Software, including but not limited to the code, documentation, 
and associated files may be copied, modified, merged, published, distributed, sublicensed, and/or sold 
without the express written permission of the copyright holder.

Unauthorized copying, modification, or distribution of this Software, its code, documentation, 
or any other associated materials, via any medium, is strictly prohibited.
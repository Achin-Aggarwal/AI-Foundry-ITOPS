# Software Assistant Bot 🤖

An intelligent chatbot built with Microsoft Bot Framework that helps users install software, answer CS/IT questions, and provide general assistance. The bot features interactive adaptive cards, database integration, and LLM-powered responses.

## Features

### 🔧 Software Installation
- **Interactive Software Catalog**: Browse available software with adaptive cards
- **Multi-version Support**: Choose from different versions of each software
- **Fuzzy Search**: Smart matching for software names (e.g., "chrome" → "Google Chrome")
- **Bulk Installation**: Install multiple software packages at once
- **Installation Simulation**: Realistic installation flow with progress updates

### 💻 CS/IT Expert Assistant
- Programming languages and concepts
- Algorithms and data structures
- Database design and management
- System architecture and design
- DevOps and cloud technologies
- Cybersecurity topics
- Machine learning and AI

### 🎯 Smart Intent Recognition
- Automatic classification of user requests
- Context-aware responses
- Fallback mechanisms for reliability

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  Intent Parser  │───▶│   Bot Handler   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   LLM (Groq)    │    │   MySQL DB      │
                       └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                             ┌─────────────────┐
                                             │ Adaptive Cards  │
                                             └─────────────────┘
```

## Prerequisites

- **Python 3.6+**
- **MySQL Database**
- **Groq API Key** (for LLM features)
- **Microsoft Bot Framework Emulator** (for testing)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd software-assistant-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the root directory:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=software_catalouge

# Groq API Configuration
GROQ_API_KEY=your_groq_api_key

# Bot Framework (Optional)
MicrosoftAppId=
MicrosoftAppPassword=
```

### 4. Database Setup
Run the database setup script:
```bash
python debug.py
```

This will:
- Create the `software_catalouge` database
- Set up the `software` table
- Populate with sample software data

### 5. Start the Bot
```bash
python app.py
```

The bot will run on `http://localhost:3978`

## Testing with Bot Framework Emulator

1. Download and install [Bot Framework Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases)
2. Launch the emulator
3. Connect to: `http://localhost:3978/api/messages`

## Usage Examples

### Software Installation
```
User: "install zoom and slack"
Bot: [Shows adaptive cards for Zoom and Slack with version options]

User: "I need software"
Bot: [Shows catalog of all available software]

User: "install chrome"
Bot: [Shows Google Chrome installation card with available versions]
```

### CS/IT Questions
```
User: "What is a binary search tree?"
Bot: [Detailed explanation with examples]

User: "How do I implement sorting algorithms?"
Bot: [Comprehensive guide with code examples]
```

### General Conversation
```
User: "Hello, how are you?"
Bot: [Friendly general response]
```

## Project Structure

```
├── app.py                 # Main application entry point
├── bot.py                 # Core bot logic and message handling
├── config.py              # Configuration settings
├── intent_parser.py       # Intent classification system
├── llm.py                 # LLM integration (Groq)
├── db_connector.py        # Database operations
├── card_builder.py        # Adaptive card creation
├── software_extractor.py  # Software name extraction
├── debug.py               # Database setup and testing
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Key Components

### Intent Parser (`intent_parser.py`)
- Classifies user messages into categories: `install`, `cs_it`, `other`
- Uses LLM for intelligent parsing with regex fallback
- Extracts specific software names from installation requests

### Database Connector (`db_connector.py`)
- MySQL integration for software catalog management
- Functions for fetching, searching, and filtering software
- Support for fuzzy search and partial matching

### Card Builder (`card_builder.py`)
- Creates interactive adaptive cards for software selection
- Handles both individual software cards and catalog browsing
- Responsive design with proper action handling

### LLM Integration (`llm.py`)
- Groq API integration using LangChain
- Specialized prompts for CS/IT questions
- Error handling and fallback mechanisms

## Database Schema

```sql
CREATE TABLE software (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    download_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);
```

## Sample Software Data

The bot comes pre-loaded with popular software including:
- **Browsers**: Google Chrome, Mozilla Firefox
- **Editors**: Visual Studio Code, PyCharm
- **Communication**: Zoom, Microsoft Teams, Slack, Discord
- **Development**: Python, Node.js, Docker, Git
- **Productivity**: Microsoft Office Suite

## API Endpoints

- `POST /api/messages` - Main bot message endpoint
- Supports Bot Framework Protocol v4

## Error Handling

- **Database Connection**: Automatic retry and fallback
- **LLM Failures**: Graceful degradation with keyword matching
- **Card Processing**: Comprehensive error messages
- **Intent Classification**: Multi-layer fallback system

## Customization

### Adding New Software
1. Connect to your MySQL database
2. Insert new records into the `software` table:
```sql
INSERT INTO software (name, version, description) 
VALUES ('Software Name', '1.0.0', 'Description');
```

### Modifying Intents
Edit `intent_parser.py` to add new intent categories or modify classification logic.

### Customizing Responses
Update prompts in `llm.py` or modify response handling in `bot.py`.

## Dependencies

```
botbuilder-integration-aiohttp>=4.14.0
langchain-groq
python-dotenv
mysql-connector-python
aiohttp
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Check the Bot Framework [documentation](https://docs.botframework.com)
- Review the [troubleshooting section](#troubleshooting)
- Open an issue in the repository

## Troubleshooting

### Common Issues

**Database Connection Error**
- Verify MySQL is running
- Check database credentials in `.env`
- Ensure database exists (run `python debug.py`)

**LLM Not Responding**
- Verify Groq API key in `.env`
- Check internet connectivity
- Monitor API rate limits

**Bot Not Starting**
- Check port 3978 is available
- Verify all dependencies are installed
- Review console output for specific errors

**Adaptive Cards Not Working**
- Ensure Bot Framework Emulator supports adaptive cards
- Check card JSON format in `card_builder.py`
- Verify bot framework version compatibility

---

🚀 **Ready to assist with software installations and technical questions!**
# VoiceMart Shopping Assistant

A comprehensive voice-powered shopping assistant that enables users to search for products using natural voice commands. The system transcribes voice input, processes queries with AI, and searches multiple e-commerce platforms to provide product recommendations.

## 🎯 Overview

VoiceMart is an AI-driven voice shopping assistant designed to make e-commerce more accessible and intuitive. It combines speech-to-text technology, natural language processing, and multi-platform product search to create a seamless voice-first shopping experience.

### Key Features

- 🎤 **Voice-to-Text Transcription**: Converts audio input to text using faster-whisper
- 🤖 **Intelligent Query Processing**: Extracts intent, entities, and filters from natural language queries
- 🔍 **Multi-Platform Product Search**: Searches Amazon, eBay, and Walmart simultaneously
- 💬 **Conversational Interface**: Maintains context across multiple interactions
- 📊 **Search History & Recommendations**: Tracks user preferences and provides personalized recommendations
- 🌐 **Multi-language Support**: Currently supports English and Sinhala (Tamil in development)
- 🎨 **Modern Web Interface**: React-based frontend with real-time voice recording

## 🏗️ Architecture

The system follows a microservices architecture with the following components:

### System Diagram
![System Architecture](https://github.com/user-attachments/assets/d61e81d9-a6a6-4bb0-80b0-65c3e70d1696)

### Sequence Diagram
![Sequence Flow](https://github.com/user-attachments/assets/ee76a1fa-7ef7-452c-b842-cad759d5987c)

### Service Components

1. **Unified Service** (Port 8000)
   - Main API gateway
   - Speech-to-text transcription
   - Query processing with LLM
   - Conversation management
   - User authentication
   - Search history tracking
   - Recommendation engine

2. **Product Finder Service** (Port 8003)
   - Product search across multiple platforms
   - Web scraping (Amazon, eBay, Walmart)
   - API integrations (eBay, Walmart APIs)
   - Hybrid search with ranking

3. **Query Processor Service** (Port 8002)
   - Intent extraction
   - Entity recognition
   - Query classification
   - Filter extraction

4. **Voice Agent Service** (Port 8001)
   - Standalone speech-to-text service
   - Audio processing

5. **Web Frontend** (Vite + React)
   - Voice recording interface
   - Product display and filtering
   - Conversation UI
   - Search history sidebar
   - Recommendation display

## 🛠️ Tech Stack

### Backend
- **Python 3.8+**
- **FastAPI** - REST API framework
- **faster-whisper** - Speech-to-text transcription
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Primary database (SQLite for development)
- **Alembic** - Database migrations
- **BeautifulSoup4** - Web scraping
- **Selenium** - Dynamic web scraping
- **scikit-learn** - Recommendation algorithms

### Frontend
- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Query** - Data fetching
- **Zustand** - State management
- **Axios** - HTTP client

## 📁 Project Structure

```
VoiceMart-Shopping-Assistant/
├── services/
│   ├── unified-service/          # Main API service
│   │   ├── app/
│   │   │   ├── main.py           # FastAPI application
│   │   │   ├── stt_engine.py     # Speech-to-text engine
│   │   │   ├── processor.py      # LLM query processor
│   │   │   ├── database.py       # Database setup
│   │   │   ├── models.py         # Data models
│   │   │   └── services/         # Business logic services
│   │   │       ├── conversation_manager.py
│   │   │       ├── recommendation_service.py
│   │   │       ├── search_history_service.py
│   │   │       └── user_service.py
│   │   ├── alembic/              # Database migrations
│   │   └── requirements.txt
│   ├── product-finder/           # Product search service
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── search_api.py
│   │   │   ├── hybrid_search.py
│   │   │   ├── scrapers/         # Web scrapers
│   │   │   └── api_clients/      # API clients
│   │   └── requirements.txt
│   ├── query-processor/          # Query processing service
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   └── processor.py
│   │   └── requirements.txt
│   └── voice-agent/              # Standalone STT service
│       ├── app/
│       │   ├── main.py
│       │   └── stt_engine.py
│       └── requirements.txt
└── voicemart-web/                # React frontend
    ├── src/
    │   ├── components/           # React components
    │   ├── pages/                # Page components
    │   ├── lib/                  # Utilities and API clients
    │   └── types/                # TypeScript types
    └── package.json
```

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 18+** and npm
- **PostgreSQL** (or SQLite for development)
- **FFmpeg** (for audio processing)
- **Git**

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install -y ffmpeg
```

**Windows:**
Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd VoiceMart-Shopping-Assistant
```

### 2. Setup Unified Service (Main Backend)

```bash
cd services/unified-service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# OR
.\venv\Scripts\Activate.ps1 # Windows (PowerShell)

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment variables
cp env_template.txt .env
# Edit .env with your configuration:
# - DATABASE_URL
# - SECRET_KEY
# - PRODUCT_FINDER_URL
# - STT_MODEL_SIZE (small, medium, large)
```

### 3. Setup Product Finder Service

```bash
cd services/product-finder

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment variables (optional - for eBay/Walmart APIs)
cp env_example.txt .env
# Add your API keys if using eBay/Walmart APIs
```

### 4. Setup Query Processor Service

```bash
cd services/query-processor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Setup Web Frontend

```bash
cd voicemart-web

# Install dependencies
npm install

# Create .env file (if needed)
# VITE_API_URL=http://localhost:8000
```

### 6. Database Setup

For PostgreSQL:
```bash
# Create database
createdb voicemart_db

# Run migrations (from unified-service directory)
cd services/unified-service
alembic upgrade head
```

For SQLite (development):
```bash
# Just set DATABASE_URL=sqlite:///./voicemart.db in .env
# Tables will be created automatically on first run
```

## 🏃 Running the Services

### Development Mode

**Terminal 1 - Unified Service (Port 8000):**
```bash
cd services/unified-service
source venv/bin/activate
python run.py
# OR
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Product Finder Service (Port 8003):**
```bash
cd services/product-finder
source venv/bin/activate
python run.py
# OR
uvicorn app.main:app --reload --port 8003
```

**Terminal 3 - Query Processor Service (Port 8002) - Optional:**
```bash
cd services/query-processor
source venv/bin/activate
uvicorn app.main:app --reload --port 8002
```

**Terminal 4 - Web Frontend:**
```bash
cd voicemart-web
npm run dev
```

### Access Points

- **Unified API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Product Finder API**: http://localhost:8003/docs
- **Web Frontend**: http://localhost:5173 (or port shown by Vite)

## 📚 API Documentation

### Unified Service Endpoints

#### Voice & Speech
- `POST /v1/stt:transcribe` - Transcribe audio to text
- `POST /v1/voice:shop` - Voice shopping (one-shot)
- `POST /v1/voice:converse` - Conversational voice shopping
- `POST /v1/voice:understand` - Complete voice understanding pipeline

#### Query Processing
- `POST /v1/query:process` - Process text query

#### Products
- `POST /v1/products:search` - Search products
- `GET /v1/products:details` - Get product details
- `GET /v1/products:categories` - Get product categories

#### User & History
- `POST /v1/auth:register` - User registration
- `POST /v1/auth:login` - User login
- `GET /v1/history:search` - Get search history
- `GET /v1/recommendations` - Get product recommendations

### Example: Voice Shopping Request

```bash
curl -X POST "http://localhost:8000/v1/voice:shop" \
  -F "file=@audio.wav" \
  -F "locale=en-US"
```

### Example: Text Query Processing

```bash
curl -X POST "http://localhost:8000/v1/query:process" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find me wireless headphones under $100",
    "locale": "en-US"
  }'
```

Full API documentation is available at http://localhost:8000/docs (Swagger UI).

## 🧪 Testing

### Test Unified Service
```bash
cd services/unified-service
source venv/bin/activate
python test_endpoints.py
python test_voice_to_products.py
```

### Test Product Finder
```bash
cd services/product-finder
source venv/bin/activate
python test_endpoints.py
python test_scrapers.py
```

### Quick Voice Test
```bash
cd services/unified-service
source venv/bin/activate
python quick_voice_test.py
```

## 🌍 Environment Variables

### Unified Service (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/voicemart_db
SECRET_KEY=your-secret-key
PRODUCT_FINDER_URL=http://localhost:8003
STT_MODEL_SIZE=small
STT_DEVICE=auto
MAX_UPLOAD_MB=25
```

### Product Finder (.env)
```env
EBAY_CLIENT_ID=your_ebay_client_id
WALMART_API_KEY=your_walmart_api_key
```

## 💼 Business Information

### Pricing Plans (in LKR)

| Plan | Features | Price (LKR) |
|------|----------|-------------|
| Basic (SME) | 1000 queries/month, Sinhala/English, basic reports | Rs. 5,000 / mo |
| Standard | 10,000 queries, multi-language, API integration | Rs. 25,000 / mo |
| Enterprise | Unlimited queries, SLA, advanced analytics | Rs. 100,000 / mo |
| Integration | Custom setup + training for enterprise deployment | Rs. 200,000 one-off |

### Target Market

- Large retailers (Keells, Cargills, Glomark)
- Online marketplaces (Kapruka, Wasi.lk)
- SMEs with Shopify/WooCommerce shops
- Regional expansion potential (Tamil Nadu, Maldives)

### Value Proposition

- Voice-based shopping → faster, easier experience
- Accessible for non-tech-savvy customers
- Sinhala + English support (Tamil in future)
- Competitive advantage for AI-driven e-commerce

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License
--

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

## 🔮 Future Enhancements

- Tamil language support
- Additional e-commerce platform integrations
- Advanced analytics dashboard
- Mobile applications (iOS/Android)
- Real-time price tracking
- Voice-activated checkout
- Multi-user conversation support

---

**Built by enithHassa & my team**

# 🏫 SGSITS Timetable Generator

A complete timetable generation system for engineering colleges with role-based access (Admin, Teacher, Student).

## 🚀 Features

- **Multi-role Authentication**: Admin, Teacher, and Student dashboards
- **Automatic Timetable Generation**: Uses intelligent scheduling algorithm
- **Teacher Conflict Prevention**: No teacher assigned to multiple classes at same time
- **Room Management**: Track room capacity and availability
- **Course Management**: Add subjects, assign teachers, create sections
- **Excel Export**: Download timetables as Excel files
- **Beautiful UI**: Space-themed modern interface with animations
- **SQLite Database**: Lightweight, no separate database server needed

## 📁 Tech Stack

**Frontend:**

- React 18 + TypeScript
- Tailwind CSS
- Vite
- Axios
- React Router DOM
- Lucide Icons
- SheetJS (Excel export)

**Backend:**

- FastAPI (Python)
- SQLite3
- JWT Authentication
- CORS enabled

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/jeorgeiiii/Time-Table-Generator.git
cd Time-Table-Generator

# Install Python dependencies
pip install fastapi uvicorn pyjwt python-multipart

# Initialize database
python reset_db.py

# Run backend server
python backend_api.py
```

## 🚀 Deployment

### Frontend (Vercel)

1. **Push to GitHub** (if not already done)
2. **Connect to Vercel**: Go to [vercel.com/new](https://vercel.com/new?teamSlug=prince-mehras-projects-a117ed40)
3. **Import your repository**
4. **Configure Environment Variables**:
   - `VITE_API_BASE_URL`: Your backend API URL (e.g., `https://your-backend.onrender.com/api`)
5. **Deploy**

### Backend (Separate Deployment)

Since Vercel doesn't natively support FastAPI, deploy the backend separately:

**Recommended Services:**

- **Railway**: `railway.app` (free tier available)
- **Render**: `render.com` (free tier available)
- **Heroku**: `heroku.com` (paid)

**Deployment Steps:**

1. Create account on chosen platform
2. Connect your GitHub repository
3. Set environment variables (copy from `.env`)
4. Deploy

**Example Railway Deployment:**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Environment Variables

**Frontend (.env):**

```
VITE_API_BASE_URL=https://your-backend-url/api
VITE_APP_NAME=Timetable Generator
```

**Backend (.env):**

```
DB_HOST=your-database-host
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=your-db-name
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📝 API Endpoints

- `POST /api/auth/login` - User login
- `POST /api/timetable/generate` - Generate timetable (Admin only)
- `GET /api/timetable/view/{branch}/{year}/{section}` - View timetable
- `GET /api/teachers` - Get all teachers
- `POST /api/admin/teachers` - Add teacher (Admin only)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

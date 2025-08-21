# הוראות בנייה והתקנה

## דרישות מערכת

### Windows
- Windows 10/11
- Visual Studio 2019 או חדש יותר (או MinGW-w64)
- CMake 3.10 או חדש יותר
- Git

### OpenCV
הפרויקט כולל את OpenCV 4.5.1 בתיקייה `my_cpp/openCV_451/`

## שלבי התקנה

### 1. שכפול הפרויקט
```bash
git clone https://github.com/chaya2350/real-time-chess.git
cd real-time-chess
```

### 2. בנייה עם Visual Studio
```bash
mkdir build
cd build
cmake .. -G "Visual Studio 16 2019" -A x64
cmake --build . --config Release
```

### 3. בנייה עם MinGW
```bash
mkdir build
cd build
cmake .. -G "MinGW Makefiles"
cmake --build . --config Release
```

### 4. הרצת המשחק
```bash
cd build
./bin/RealTimeChess.exe
```

## פתרון בעיות נפוצות

### שגיאת OpenCV
אם יש בעיה עם OpenCV, ודא ש:
- התיקייה `my_cpp/openCV_451/` קיימת
- קבצי ה-DLL נמצאים ב-PATH או בתיקיית ההרצה

### שגיאת CMake
```bash
# נקה את תיקיית הבנייה
rm -rf build
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
```

### שגיאות קומפילציה
ודא שאתה משתמש ב-C++17:
```bash
cmake .. -DCMAKE_CXX_STANDARD=17
```

## הרצה במצב Debug
```bash
cmake --build . --config Debug
./bin/RealTimeChess.exe
```

## מבנה קבצים אחרי בנייה
```
build/
├── bin/
│   └── RealTimeChess.exe
├── pieces/          # הועתק אוטומטית
├── pic/            # הועתק אוטומטית  
└── sounds/         # הועתק אוטומטית
```

## הערות נוספות
- המשחק מחפש את קבצי המשאבים בנתיבים יחסיים
- ודא שקבצי ה-DLL של OpenCV נגישים
- לביצועים מיטביים, השתמש במצב Release
# theme.py
def load_theme():
    return """
    <style>
    :root{
      --bg-1:#FFDEE9;           /* soft pink */
      --bg-2:#B5FFFC;           /* aqua mint */
      --primary:#FF6B6B;        /* coral red */
      --secondary:#FFD93D;      /* bright yellow */
      --accent:#4C9AFF;         /* sky blue accent */
      --text:#1A1A1A;           /* dark text for contrast */
      --muted:#555555;
      --success:#2ECC71;        /* bright green */
      --error:#E74C3C;          /* vivid red */
      --glass:rgba(255,255,255,0.65);
      --glass-border:rgba(255,255,255,0.85);
      --shadow:0 8px 24px rgba(0,0,0,0.15);
      --radius:14px;
    }

    /* Global background with bright gradient */
    html, body, [data-testid="stAppViewContainer"]{
      background: linear-gradient(135deg, var(--bg-1), var(--bg-2));
      color: var(--text);
    }

    /* Typography */
    h1,h2,h3,h4 { color: var(--primary); letter-spacing: 0.5px; }
    p, span, li { color: var(--muted); }

    /* Left sidebar (native) */
    [data-testid="stSidebar"]{
      background: linear-gradient(180deg, #FFF9E3, #FFE3E3);
      border-right: 2px solid var(--accent);
      box-shadow: var(--shadow);
    }
    [data-testid="stSidebar"] * { color: var(--text); }

    /* Right column container — glass panel look */
    .right-glass{
      background: var(--glass);
      backdrop-filter: blur(12px);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 16px;
    }

    /* Expanders */
    [data-testid="stExpander"]{
      background: var(--glass);
      border: 1px solid var(--accent);
      border-radius: var(--radius);
      overflow: hidden;
    }
    [data-testid="stExpander"] details summary{
      color: var(--primary);
      font-weight: bold;
    }

    /* Primary button style */
    .stButton > button{
      background: linear-gradient(135deg, var(--primary), var(--secondary));
      color: white;
      border: 0;
      border-radius: 12px;
      padding: 10px 16px;
      font-weight: 700;
      box-shadow: 0 6px 12px rgba(0,0,0,0.2);
      transition: transform .06s ease, box-shadow .2s ease, filter .2s ease;
    }
    .stButton > button:hover{
      transform: translateY(-2px);
      filter: brightness(1.1);
      box-shadow: 0 10px 20px rgba(0,0,0,0.25);
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stPasswordInput > div > div > input{
      background: #FFF9E3;
      color: var(--text);
      border: 1px solid var(--accent);
      border-radius: 10px;
    }
    .stTextInput > div > div > input::placeholder{
      color: #999999;
    }

    /* Status messages */
    .stAlert{ border-radius: 12px; }
    .stAlert[data-baseweb="notification"] [data-testid="stMarkdownContainer"] p{ color: var(--text); }
    .stAlert div[role="alert"]{ backdrop-filter: blur(6px); }

    /* Tables */
    .stDataFrame, .stTable{
      background: #FFFFFF;
      border: 1px solid var(--accent);
      border-radius: var(--radius);
      overflow: hidden;
    }

    /* Footer */
    .eduhub-footer{
      position: fixed; bottom: 0; left: 0; right: 0;
      background: linear-gradient(90deg, var(--secondary), var(--primary));
      color: white;
      text-align: center;
      padding: 8px 10px;
      border-top: 2px solid var(--accent);
      font-weight: bold;
    }

    /* Accent underline for section titles */
    .underline-accent{
      border-bottom: 3px solid var(--accent);
      padding-bottom: 4px;
      display: inline-block;
      color: var(--primary);
    }

    /* Dashboard link */
    #custom-dashboard-link{
      position: absolute; top: 10px; right: 20px;
      background: linear-gradient(135deg, var(--secondary), var(--primary));
      color: white; padding: 8px 14px; border-radius: 10px;
      text-decoration: none; font-weight: 700;
      border: 1px solid var(--accent);
      box-shadow: 0 6px 12px rgba(0,0,0,0.2);
      transition: transform .06s ease, box-shadow .2s ease, filter .2s ease;
    }
    #custom-dashboard-link:hover{ transform: translateY(-2px); filter: brightness(1.1); }

    /* Subject tags */
    .subject-btn{
      margin: 6px; padding: 8px 14px;
      border: 1px solid var(--accent);
      background: #FFF9E3;
      color: var(--text); border-radius: 10px; display: inline-block;
      font-weight: 600; transition: all .2s ease;
    }
    .subject-btn:hover{ background: var(--secondary); color: white; }
    .subject-btn.selected{
      background: linear-gradient(135deg, var(--primary), var(--secondary));
      color: white; border-color: transparent;
    }
    </style>
    """

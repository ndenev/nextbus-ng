from nextbus import app
from nextbus.common.config import APP_CONFIG

def main():
    app.run(debug=APP_CONFIG['flask_debug'],
            host=APP_CONFIG['flask_host'],
            port=APP_CONFIG['flask_port'])

if __name__ == '__main__':
    main()


from app import create_app

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    # Run the app on localhost:5000 with debug mode enabled
    app.run(debug=True, host="localhost", port=5000)
    
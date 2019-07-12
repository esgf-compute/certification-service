if __name__ == '__main__':
    from certification_service import create_app

    app = create_app()

    app.run(host='0.0.0.0', debug=True)

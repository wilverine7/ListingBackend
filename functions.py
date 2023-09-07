def removeBackground(url, imageName):
    from app import app  
    import pysftp
    import requests
    from PIL import Image
    from io import BytesIO
    from datetime import datetime
    import rembg
    app.logger.info("Removing background from image")
    try:
        # set up variables to create file names and connect to server
        image_url = url
        imageName = imageName
        # Access configuration values using app.config
        hostname = app.config["HOSTNAME"]
        username = app.config["USERNAME"]
        password = app.config["PASSWORD"]
    except Exception as e:
        app.logger.error("Error getting configuration values")
        app.logger.error(f"Error: {str(e)}")
        error = "There was an error getting the configuration values"
        json_error = {"error": error}
        return json_error

    folder_name = datetime.today().strftime("%Y-%m-%d")
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    server_path = f"public_html/media/L9/{folder_name}/{imageName}.jpg"
    try:
        with pysftp.Connection(
            hostname, username=username, password=password, cnopts=cnopts
        ) as sftp:
            app.logger.info("Connected to server")
            with sftp.cd("public_html/media/L9/"):
                if sftp.exists(folder_name):
                    pass
                else:
                    # create new directory at public_html/media/L9/ with the folder_name variable
                    sftp.mkdir(folder_name)
            try:
                # open the image from the url
                app.logger.info(f"Opening image from url: {image_url}")
                response = requests.get(image_url, stream=True)
                # convert the image to a PIL image
                image = Image.open(BytesIO(response.content))

                try:
                    # remove background from image
                    image = rembg.remove(image)
                except Exception as e:
                    print(f"Error: {str(e)}")
                    error = "There was an error removing the background"
                    json_error = {"error": error}
                    app.logger.error("Error removing background")
                    return json_error

                # creates a file like object to save the image to
                image_io = BytesIO()
                # saves the image with no background as a png
                image.save(image_io, format="PNG")

                # open it again with PIL so we can process it
                image2 = Image.open(image_io)
                h, w = image2.size
                if h > w:
                    imageSize = (h, h)
                else:
                    imageSize = (w, w)

                # Create a new square image with a white background
                square_image = Image.new("RGBA", (imageSize), (255, 255, 255, 0))

                # Calculate the position to center the original image on the new canvas
                position = (
                    (square_image.width - image2.width) // 2,
                    (square_image.height - image2.height) // 2,
                )

                # Paste the original image into the center of the square image
                square_image.paste(image2, position, image2)

                # convert the image to RGB
                square_image = square_image.convert("RGB")

                square_image = square_image.resize((1200, 1200))

                image_io2 = BytesIO()
                # Save the resized image to a file-like object
                square_image.save(image_io2, format="JPEG")

                # Upload the image to the server
                image_io2.seek(0)  # Reset the file pointer to the beginning
                sftp.putfo(image_io2, server_path)

                # close connection
                sftp.close()

                # creates a variable to pass to the html page to display the image and url
                BikeWagonUrl = (
                    f"https://bikewagonmedia.com/media/L9/{folder_name}/{imageName}.jpg"
                )
                app.logger.info("Background removed successfully")
                return BikeWagonUrl
            except Exception as e:
                print(f"Error: {str(e)}")
                error = "There was an error processing the image"
                json_error = {"error": error}
                app.logger.error("Error processing image")
                return json_error
    except Exception as e:
        print(f"Error: {str(e)}")
        error = "There was an error connecting to the server in remove background"
        json_error = {"error": error}
        app.logger.error("Error connecting to server in remove background")
        return json_error
    

def process_image(image):
    from PIL import Image
    from io import BytesIO

    # Determine the new size of the square image
    max_size = max(image.size[0], image.size[1])
    square_size = (max_size, max_size)

    # Create a new square image with a white background
    square_image = Image.new("RGBA", square_size, (255, 255, 255))

    # Determine the offset to place the original image in the center of the square image
    x_offset = int((square_size[0] - image.size[0]) / 2)
    y_offset = int((square_size[1] - image.size[1]) / 2)

    try:
        # Paste the original image into the center of the square image
        square_image.paste(image, (x_offset, y_offset), image)
    except Exception as e:
        print(e)
    # Resize the square image to be 1200 x 1200
    image_resized = square_image.resize((1200, 1200))

    # Save the resized image to a file-like object
    image_io = BytesIO()
    image_resized.convert("RGB").save(image_io, "JPEG")

    # Upload the image to the server
    image_io.seek(0)  # Reset the file pointer to the beginning

    return image_io

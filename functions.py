def removeBackground(image):
    from app import app
    from PIL import Image
    from io import BytesIO
    import rembg

    app.logger.info("Removing background from image")
    try:
        try:
            # remove background from image
            image = rembg.remove(image)
            app.logger.info("Background removed successfully")
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
        return image_io2
    except Exception as e:
        print(f"Error: {str(e)}")
        error = "There was an error processing the image"
        json_error = {"error": error}
        app.logger.error("Error processing image")
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


def twoItemSkiPackageBuilder(ski, boot):
    from PIL import Image

    ski = pilOpener(ski)
    boot = pilOpener(boot)

    # create a new blank white image
    package = Image.new("RGB", (1200, 1200), (255, 255, 255))

    # find the middle point of the ski image
    skiWidth, skiHeight = ski.size
    skiThird = skiWidth / 2.5

    # crop the ski image down the middle
    ski = ski.crop((skiThird, 0, skiWidth, skiHeight))
    skiWidth, skiHeight = ski.size

    # resize the cropped ski mainting the aspect ratio
    ski = ski.resize((int(skiWidth * 1200 / skiHeight), 1200))

    # paste that ski image on the left side of the package image
    package.paste(ski, (0, 0))

    # resize the boot image to 600x600
    boot = boot.resize((600, 600))

    # paste the boot image on the top right side of the package image
    package.paste(boot, (600, 300))
    return package


def twoItemBoardPackageBuilder(board, boardBindings):
    from PIL import Image

    board = pilOpener(board)
    boardBindings = pilOpener(boardBindings)

    # create a new blank white image
    package = Image.new("RGB", (1200, 1200), (255, 255, 255))

    # calculate 25% of the image width
    removal = board.size[0] * 0.25
    # get image width
    boardWidth, boardHeight = board.size

    # crop 25% of px from each side of the board
    board = board.crop((removal, 0, (boardWidth - removal), boardHeight))

    # paste that board image on the left side of the package image
    package.paste(board, (0, 0))

    # resize the boardBindings image to 600x600
    boardBindings = boardBindings.resize((600, 600))

    # paste the boardBindings image on the top right side of the package image
    package.paste(boardBindings, (600, 300))
    return package


def boardPackageBuilder(board, boardBindings, snowboardBoots):
    from PIL import Image

    board = pilOpener(board)
    snowboardBoots = pilOpener(snowboardBoots)
    boardBindings = pilOpener(boardBindings)

    # create a new blank white image
    package = Image.new("RGB", (1200, 1200), (255, 255, 255))

    # calculate 25% of the image width
    removal = board.size[0] * 0.25
    # get image width
    boardWidth, boardHeight = board.size

    # crop 25% of px from each side of the board
    board = board.crop((removal, 0, (boardWidth - removal), boardHeight))

    # paste that board image on the left side of the package image
    package.paste(board, (0, 0))

    # resize the snowboardBoots image to 600x600
    snowboardBoots = snowboardBoots.resize((600, 600))

    # paste the snowboardBoots image on the top right side of the package image
    package.paste(snowboardBoots, (600, 0))

    # resize the boardBindings image to 600x600
    boardBindings = boardBindings.resize((600, 600))

    # paste the boardBindings image on the bottom right side of the package image
    package.paste(boardBindings, (600, 600))
    return package


def skiPackageBuilder(ski, boot, binding):
    from PIL import Image

    ski = pilOpener(ski)
    boot = pilOpener(boot)
    binding = pilOpener(binding)

    # create a new blank white image
    package = Image.new("RGB", (1200, 1200), (255, 255, 255))

    # find the third point of the ski image
    skiWidth, skiHeight = ski.size
    skiThird = skiWidth / 2.5

    # crop the ski image down the middle
    ski = ski.crop((skiThird, 0, skiWidth, skiHeight))
    skiWidth, skiHeight = ski.size

    # resize the cropped ski mainting the aspect ratio
    ski = ski.resize((int(skiWidth * 1200 / skiHeight), 1200))

    # paste that ski image on the left side of the package image
    package.paste(ski, (0, 0))

    # resize the boot image to 600x600
    boot = boot.resize((600, 600))

    # paste the boot image on the top right side of the package image
    package.paste(boot, (600, 0))

    # resize the binding image to 600x600
    binding = binding.resize((600, 600))

    # paste the binding image on the bottom right side of the package image
    package.paste(binding, (600, 600))
    return package


def skiBuilder(unbuiltSki):
    from PIL import Image

    unbuiltSki = pilOpener(unbuiltSki)

    # Determine the new size of the square image
    max_size = max(unbuiltSki.size[0], unbuiltSki.size[1])
    square_size = (max_size, max_size)

    # Create a new square image with a white background
    square_image = Image.new("RGB", square_size, (255, 255, 255))

    # Determine the offset to place the original image in the center of the square image
    x_offset = int((square_size[0] - unbuiltSki.size[0]) / 2)
    y_offset = int((square_size[1] - unbuiltSki.size[1]) / 2)

    # Paste the original image into the center of the square image
    square_image.paste(unbuiltSki, (x_offset, y_offset), unbuiltSki)

    # create a new blank white image
    package = Image.new("RGB", (1200, 1200), (255, 255, 255))

    # find the horizontal middle point of the ski image
    skiWidth, skiHeight = square_image.size
    skiHorizontalMiddle = skiHeight / 2
    skiVerticalMiddle = skiWidth / 2

    # find 25% of the ski width
    skiRemoval = skiWidth * 0.38

    singleSki = square_image.crop((skiRemoval, 0, skiVerticalMiddle, skiHeight))
    singleSkiWidth, singleSkiHeight = singleSki.size

    # crop the ski image down the middle
    bottomSki = singleSki.crop(
        (0, skiHorizontalMiddle, singleSkiWidth, singleSkiHeight)
    )
    topSki = singleSki.crop((0, 0, singleSkiWidth, skiHorizontalMiddle))

    # resize the ski to so the height is 1200 but width is proportional
    ski = square_image.resize((int(skiWidth * 1200 / skiHeight), 1200))

    skiRemoval = ski.size[0] * 0.35
    # crop the extra white off the image
    ski = ski.crop((skiRemoval, 0, 1200 - skiRemoval, 1200))

    # resize the bottomSki to have height of 1100 but make sure the image is proportional
    bottomSkiWidth, bottomSkiHeight = bottomSki.size
    aspect_ratio = bottomSkiWidth / bottomSkiHeight
    new_width = int(1150 * aspect_ratio)
    bottomSki = bottomSki.resize((new_width, 1150))

    # resize the topSki to have height of 1100 with proportional width
    topSkiWidth, topSkiHeight = topSki.size
    aspect_ratio = topSkiWidth / topSkiHeight
    new_width = int(1150 * aspect_ratio)
    topSki = topSki.resize((new_width, 1150))
    topSkiWidth, topSkiHeight = topSki.size

    # paste that ski image on the left side of the package image
    package.paste(ski, (0, 0))

    # paste the topSki image on the bottom right side of the package image
    package.paste(topSki, (500, 100))

    # paste the bottomSki image on the top right side of the package image
    package.paste(bottomSki, (500 + topSkiWidth, 0))
    return package


def pilOpener(image):
    import requests
    from PIL import Image
    from io import BytesIO

    try:
        response = requests.get(image, stream=True)
        pilImage = Image.open(BytesIO(response.content)).convert("RGBA")
    except:
        pilImage = Image.open(image).convert("RGBA")

    return pilImage


def getToken():
    import requests
    import credentials as cred

    url = "https://api.channeladvisor.com/oauth2/token"

    payload = f"grant_type=refresh_token&refresh_token={cred.ca_refresh_token}"
    headers = {
        "Authorization": f"Basic {cred.ca_auth_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    token = response.json()["access_token"]
    return token


def caUpload(sku, imageUrl, imageNum):
    import requests

    ca_auth_token = getToken()
    url = "https://api.channeladvisor.com/v1/Products"
    params = {"$filter": f"Sku eq '{sku}'", "$select": "ID"}
    headers = {
        "Authorization": f"Bearer {ca_auth_token}",
        "Content-Type": "application/json",
    }
    r = requests.get(url=url, headers=headers, params=params)
    data = r.json()
    CaId = data["value"][0]["ID"]

    # url = f"https://api.channeladvisor.com/v1/Products({CaId})/Images('ITEMIMAGEURL{imageNum}')"
    url = f"https://api.channeladvisor.com/v1/Images(ProductID={CaId},PlacementName='ITEMIMAGEURL{imageNum}')"
    payload = {"Url": imageUrl}
    response = requests.put(url, headers=headers, json=payload)
    print("done")
    if response.status_code == 204:
        print("Image updated successfully.")
        return "success"
    else:
        error = f"Request failed with status code {response.status_code}")
        print("Response:", response.text)
        return(error, response.text)

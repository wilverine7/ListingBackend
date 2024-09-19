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


def getToken(ca_refresh_token, ca_auth_token):
    import requests
    import time

    retryCount = 0

    url = "https://api.channeladvisor.com/oauth2/token"

    payload = f"grant_type=refresh_token&refresh_token={ca_refresh_token}"
    headers = {
        "Authorization": f"Basic {ca_auth_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    while retryCount < 6:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            token = response.json()["access_token"]
            return token
        elif response.status_code == 429:
            time.sleep(15)
        else:
            error = f"Request failed with status code {response.status_code}"
        retryCount += 1

    return error


def caUpload(sku, imageUrl, imageNum, auth_token):
    import requests
    import time
    from app import logger

    retryCount = 0

    url = "https://api.channeladvisor.com/v1/Products"
    params = {"$filter": f"Sku eq '{sku}'", "$select": "ID"}
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }
    while retryCount < 6:
        r = requests.get(
            url=url,
            headers=headers,
            params=params,
        )
        retryCount += 1
        try:
            data = r.json()
        except:
            data = {"value": []}
        if r.status_code == 200 and data["value"] != []:
            CaId = data["value"][0]["ID"]
            error = ""
            break
        elif r.status_code == 429:
            time.sleep(10)
            logger.info("waiting")
        else:
            error = f"Request failed with status code {r.status_code}"
    if error != "":
        return error

    retryCount = 0
    url = f"https://api.channeladvisor.com/v1/Images(ProductID={CaId},PlacementName='ITEMIMAGEURL{imageNum}')"
    payload = {"Url": imageUrl}
    while retryCount < 6:
        response = requests.put(url, headers=headers, json=payload)
        retryCount += 1
        if response.status_code == 204:
            return "success"
        elif response.status_code == 429:
            # try again in 10 seconds
            time.sleep(10)
            logger.info("429 - Waiting")
            error = f"Request failed with status code {response.status_code}"
        else:
            error = f"Request failed with status code {response.status_code}"
            logger.error(response.status_code, response.text)
    return (error, response.text)


def singleSkiFileBuilder(df, app, folder):
    from flask import Flask, request, Response, jsonify
    import pandas as pd
    from flask_cors import CORS, cross_origin
    from datetime import datetime
    import os
    import json
    from datetime import datetime
    from io import BytesIO
    import functions as fn
    import requests
    import pysftp
    from PIL import Image
    from openpyxl.workbook import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from flask_api import status
    from openpyxl.worksheet.datavalidation import DataValidation
    import gspread
    import logging
    import sys
    import time

    df = df[df["VARIATION_PARENT_SKU"] != "Parent"]
    uniqueCombo = df["VARIATION_PARENT_SKU"].unique()
    folder_name = datetime.today().strftime("%Y-%m-%d")

    hostname = app.config["HOSTNAME"]
    username = app.config["USERNAME"]
    password = app.config["PASSWORD"]

    columns = []
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    try:
        with pysftp.Connection(
            hostname,
            username=username,
            password=password,
            cnopts=cnopts,
        ) as sftp:
            app.logger.info("Connected to FTP server")
            with sftp.cd("public_html/media/L9/"):
                if sftp.exists(folder_name) == False:
                    # create new directory at public_html/media/L9/ with the folder_name variable
                    sftp.mkdir(folder_name)
                    app.logger.info("Created new folder")

            try:
                # getting the uniqueSku problem is you download images multiple times
                for combo in uniqueCombo:
                    comboDf = df[df["VARIATION_PARENT_SKU"] == combo]
                    sku = combo
                    comboDf.reset_index(drop=True, inplace=True)
                    packageType = comboDf["SKI/BOARD"][0].upper()
                    if comboDf["SKI/BOARD"][0].upper() == "SKI":
                        packageType = "Ski"
                    elif comboDf["SKI/BOARD"][0].upper() == "BOARD":
                        packageType = "Board"
                    else:
                        error = "There is an error with the Ski/Board column. Please make sure all values are either Ski or Board."
                        return (error, status.HTTP_400_BAD_REQUEST)
                    imagePath = comboDf["MAIN_IMAGE_URL"][0]
                    try:
                        r = requests.get(imagePath, stream=True)
                    except:
                        status_code = 500
                    else:
                        status_code = r.status_code
                    if status_code != 200:
                        # if the imagePath contains a . split the string and get everything before the .
                        if "." in imagePath:
                            fileName = imagePath.split(".")[0]
                            fileName = fileName.strip()
                        else:
                            fileName = imagePath
                            fileName = fileName.strip()

                        for file in folder:
                            imageName = file.filename.rsplit("/", 1)[-1]
                            # remove the file extenstion from the imageName
                            imageName = imageName.split(".")[0]

                            if imageName == fileName:
                                imagePath = file
                    packageImage = skiBuilder(imagePath)

                    image_io = BytesIO()
                    packageImage.convert("RGB").save(image_io, "JPEG")

                    # Upload the image to the server
                    image_io.seek(0)  # Reset the file pointer to the beginning

                    imageNumber = 1
                    folder_name = datetime.today().strftime("%Y-%m-%d")
                    server_path = (
                        f"public_html/media/L9/{folder_name}/{sku}_Img{imageNumber}.jpg"
                    )
                    sftp.putfo(image_io, server_path)
                    BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_Img{imageNumber}.jpg"
                    df.loc[
                        df["VARIATION_PARENT_SKU"] == combo,
                        "Server Image 1",
                    ] = BikeWagonUrl

            except Exception as e:
                print(e)
    except Exception as e:
        print(e)
    df = df.rename(columns={"VARIATION_PARENT_SKU": "PARENT_SKU_COLOR"})
    df["PARENT_SKU"] = df["PARENT_SKU_COLOR"]
    df.dropna(subset=["Server Image 1"], inplace=True)

    df.set_index("PARENT_SKU_COLOR", inplace=True)
    dfJson = df.to_json(orient="index")
    ResponseData = {"df": dfJson}
    return ResponseData

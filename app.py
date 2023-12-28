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


pd.options.mode.chained_assignment = None  # default='warn'

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(28)
app.config["HOSTNAME"] = os.environ["FLASK_HOSTNAME"]
app.config["USERNAME"] = os.environ["FLASK_USERNAME"]
app.config["PASSWORD"] = os.environ["FLASK_PASSWORD"]
app.config["GSHEETSKEY"] = os.environ["FLASK_GSHEETS_KEY"]

# import credentials
# app.config["HOSTNAME"] = credentials.hostname
# app.config["USERNAME"] = credentials.username
# app.config["PASSWORD"] = credentials.password
# app.config["GSHEETSKEY"] = credentials.gsheetskey

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# logging.basicConfig(filename='DebugLogs.log', encoding='utf-8', level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# Set the logging level to DEBUG so that it logs all messages.
app.logger.setLevel(logging.DEBUG)

# Create a log file and configure the file handler.
log_handler = logging.FileHandler("app.log")
log_handler.setLevel(logging.DEBUG)

# Create a formatter to format log messages.
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_handler.setFormatter(formatter)

# Add the file handler to the app's logger.
app.logger.addHandler(log_handler)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    app.logger.error(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    )


sys.excepthook = handle_exception


@app.route("/", methods=["GET"])
def index():
    json = {"status": 200, "message": "This is a running API!"}
    return jsonify(json)


# used
## endpoint for uploading an elastic listing file
@app.route("/ListingUpload", methods=["POST", "GET"])
def ListingUpload():
    if request.method == "GET":
        return "Upload a file using the API"

    # post
    file = request.files["file"]
    elasticBool = request.form["elasticBool"]

    # Save the file locally
    file.save("uploaded_file.xlsx")

    # Read the Excel file into a Pandas DataFrame
    df = pd.read_excel("uploaded_file.xlsx")
    if "Primary Category" not in df.columns:
        error = "Primary Category column not found"
        return error, status.HTTP_400_BAD_REQUEST
    if elasticBool == "true":
        # SalesForce
        SalesForceDf = pd.read_excel("/Users/wilverine7/Desktop/Salesforce.xlsx")

        for x in range(len(df)):
            if df["Color Name"][x] == "No Color":
                df.at[x, "Color Name"] = ""
            if df["Size"][x] == "1SZ":
                df.at[x, "Size"] = ""
            if "Category" in df.columns:
                if df["Category"][x] == "Skis" and df["Size"][x] != "":
                    df.at[x, "Size"] = f"{df['Size'][x]}cm"
            PONumber = df["PO #"][x]
            PONumber = PONumber.split("-")[0]
            df.at[x, "PO #"] = PONumber

        # build new df that has all the columns we want for sku creation
        newDf = pd.DataFrame(
            columns=[
                "Existing Sku",
                "SKU",
                "Existing Parent SKU",
                "Title",
                "Manufacturer Title",
                "Model Name",
                "Primary Color",
                "Config Color",
                "Size",
                "Gender",
                "Sport",
                "Primary Category",
                "Classification",
                "Brand",
                "Quantity",
                "Cost",
                "Wholesale Cost",
                "Sale Price",
                "Retail Price",
                "MAP Price",
                "Price LS",
                "UPC",
                "EAN",
                "MPN",
                "Supplier",
                "Supplier Part Number",
                "PO Number",
                "Sales Opportunity",
                "MAP Restrictions",
                "Selling Channels",
                "Territories",
                "Inventory",
                "Type",
                "Reorder Point",
                "Model Year",
            ]
        )
        # all data that gets moved over simply just copy over
        newDf["PO Number"] = df["PO #"]
        newDf["Sales Opportunity"] = df["PO #"]
        newDf["Model"] = df["Style Name"]
        newDf["MPN"] = df["SKU"]
        newDf["Part Number"] = df["SKU"]
        newDf["Wholesale Cost"] = df["Wholesale Price"]
        newDf["Retail Price"] = df["Retail Price"]
        newDf["Quantity"] = df["Quantity Requested"]
        newDf["Color"] = df["Color Name"]
        newDf["Size"] = df["Size"]
        newDf.fillna("", inplace=True)

        # Check Length <=10 then delete, 11 =12 UPC, 13-15 EAN, > 15 Delete, IF (ISNUMBER=FALSE, DELETE)
        for x in range(len(df)):
            if len(str(df["UPC"][x])) > 15 or len(str(df["UPC"][x])) <= 10:
                newDf.at[x, "UPC"] = df["UPC"][x].astype(str)
                newDf.at[x, "EAN"] = df["UPC"][x].astype(str)

            elif len(str(df["UPC"][x])) >= 13:
                newDf.at[x, "EAN"] = df["UPC"][x].astype(str)
                newDf.at[x, "UPC"] = ""

            elif len(str(df["UPC"][x])) >= 11:
                newDf.at[x, "UPC"] = df["UPC"][x].astype(str)
                newDf.at[x, "EAN"] = ""

        # convert unisex to Men's, Women's
        for x in range(len(df)):
            string = df["Gender"][x]
            if string.find("Unisex") != -1:
                string = string.replace("Unisex", "Men's, Women's")
                df.at[x, "Gender"] = string
            df["Gender"][x]
            newDf["Gender"] = df["Gender"]

        PO = newDf["PO Number"][0]

        for x in range(len(SalesForceDf["Sales Opp. Number"])):
            string = SalesForceDf["Sales Opp. Number"][x]
            N = 5
            # get length of string
            length = len(string)

            # create a new string of last N characters
            Str2 = "L9" + string[length - N :]
            SalesForceDf.at[x, "PO Number"] = Str2
            if Str2 == PO:
                print("found")
                newDf["MAP Restrictions"] = SalesForceDf.at[x, "MAP Restrictions"]
                newDf["Supplier"] = SalesForceDf.at[x, "Supplier Name"]
                newDf["Brand"] = SalesForceDf.at[x, "Supplier.Brands"]

                # territroy restrictions
                if SalesForceDf["Territory Restrictions"][x] == "3 - No Restrictions":
                    newDf[
                        "Territories"
                    ] = "Argentina;Australia;Chile;Ireland;Japan;New Zealand;UK;United States;Canada"
                elif SalesForceDf["Territory Restrictions"][x] == "2 - Other":
                    newDf["Territories"] = "United States; Canada"
                elif SalesForceDf["Territory Restrictions"][x] == "1 - US Only":
                    newDf["Territories"] = "United States"
        newDf["Primary Category"] = df["Primary Category"]
        primaryDf = newDf.copy()
    else:
        primaryDf = df.copy()

    # this is the category to attribute set sheet
    # open Attribute Set Attribute sheet and convert it to a DF
    attributeUrl = "https://docs.google.com/spreadsheets/d/1tXm039Fcj16Qn1rWd6HzpyoqQ_l0H64tlmV_0nVDmIk/edit#gid=626682809"
    sa = gspread.service_account_from_dict(app.config["GSHEETSKEY"])
    sh = sa.open_by_url(attributeUrl)
    ws = sh.worksheet("PrimaryToAttributeSet")
    primaryToAttributeDf = pd.DataFrame(ws.get_all_records())

    # this is the sheet with attribute values that will populate dropdowns
    ws = sh.worksheet("Attribute Values")
    attributeValuesDf = pd.DataFrame(ws.get_all_records())

    # create a copy of the original sheet
    wb = Workbook()
    openpyxl_ws = wb.active
    copySheet = wb.create_sheet(title="CopyOfOriginal")
    for r in dataframe_to_rows(primaryDf, index=False, header=True):
        copySheet.append(r)

    # drop rows where Primary Category is null
    primaryDf = primaryDf.dropna(subset=["Primary Category"])

    # get the categories from the listing sheet
    categories = primaryDf["Primary Category"].unique()

    # maxx keeps track of the total attribute name columns added so we can know how many attribute value columns we need to add
    maxx = 0
    # build the attribute set columns in the listing sheet
    for category in categories:
        # get just the row that matches the category
        attributeDf = primaryToAttributeDf[
            primaryToAttributeDf["Primary Category"] == category
        ]
        attributeDf = attributeDf.replace("", pd.NA)
        attributeDf = attributeDf.dropna(axis=1)
        x = 1

        # loop through the columns and get the attribute names
        attributeValueList = []
        for columnName in attributeDf.columns:
            if columnName == f"attribute_id {x}":
                # get the attribute name
                name = attributeDf[columnName].iloc[0]

                # add the attribute name to the listing sheet
                primaryDf.loc[
                    primaryDf["Primary Category"] == category, [f"Attribute{x}Name"]
                ] = name
                x += 1
                if maxx < x:
                    maxx = x

    # convert primarydf to openpyxl, get the column header and if it matches f"Attribute{x}Name"
    # then get the cell below. Add a new column next to it that is datavalidation with the values coming from the attribute values sheet
    for r in dataframe_to_rows(primaryDf, index=False, header=True):
        openpyxl_ws.append(r)
    x = 1
    maxcol = openpyxl_ws.max_column
    columnNumber = 1
    NewSheet = wb.create_sheet(title="attributeValue")
    attribute = ""
    for column in range(1, maxcol + maxx + 1):
        cell = openpyxl_ws.cell(row=1, column=column)

        if cell.value == f"Attribute{x}Name":
            openpyxl_ws.insert_cols(column + 1)
            cell = openpyxl_ws.cell(row=1, column=column + 1)
            cell.value = f"Attribute{x}Value"
            row = 2
            while row <= openpyxl_ws.max_row:
                # for row in range(2, openpyxl_ws.max_row + 1):
                attribute = openpyxl_ws.cell(row=row, column=column)
                print(attribute.value)

                # if the cell before is the same as the current cell then we can reuse the datavalidation formula
                if (
                    attribute.value
                    == openpyxl_ws.cell(row=row - 1, column=column).value
                ):
                    dv = DataValidation(
                        type="list",
                        formula1=formula,
                        allow_blank=True,
                    )
                    # Optionally set a custom error message
                    dv.error = "Your entry is not in the list"
                    dv.errorTitle = "Invalid Entry"
                    # Optionally set a custom prompt message
                    dv.prompt = "Please select from the list"
                    dv.promptTitle = "List Selection"

                    # add the data validation to only the cell next to the current cell
                    cell = openpyxl_ws.cell(row=row, column=column + 1)
                    openpyxl_ws.add_data_validation(dv)
                    dv.add(cell)
                    row += 1

                # if the cells don't match we need to get new values to build the data validation
                else:
                    # print(attribute.value)
                    filteredDf = attributeValuesDf[
                        attributeValuesDf["name"] == attribute.value
                    ]
                    if not filteredDf.empty:
                        # print(filteredDf)
                        filteredDf.replace("", pd.NA, inplace=True)
                        filteredDf.dropna(axis=1, inplace=True)
                        count = 1
                        attributeValueList = []
                        for columnName in filteredDf.columns:
                            if columnName == f"attribute_value {count}":
                                attributeValueList.append(
                                    filteredDf[columnName].iloc[0]
                                )

                                count += 1
                        print(attributeValueList)

                        for printRow in range(len(attributeValueList)):
                            cell = NewSheet.cell(row=printRow + 1, column=columnNumber)
                            cell.value = attributeValueList[printRow]
                            maxRow = printRow + 1

                        ColumnLetter = openpyxl_ws.cell(
                            row=1, column=columnNumber
                        ).column_letter
                        columnNumber = columnNumber + 1
                        formula = (
                            f"attributeValue!{ColumnLetter}1:{ColumnLetter}{maxRow}"
                        )
                        dv = DataValidation(
                            type="list",
                            formula1=formula,
                            allow_blank=True,
                        )
                        # Optionally set a custom error message
                        dv.error = "Your entry is not in the list"
                        dv.errorTitle = "Invalid Entry"
                        # Optionally set a custom prompt message
                        dv.prompt = "Please select from the list"
                        dv.promptTitle = "List Selection"

                        # add the data validation to only the cell next to the current cell
                        cell = openpyxl_ws.cell(row=row, column=column + 1)
                        openpyxl_ws.add_data_validation(dv)
                        dv.add(cell)
                        row += 1

                    else:
                        # if the attribute isn't in the attribute value sheet then just add a blank data validation
                        formula = ""
                        dv = DataValidation(
                            type="list",
                            formula1=formula,
                            allow_blank=True,
                        )
                        # Optionally set a custom error message
                        dv.error = "Your entry is not in the list"
                        dv.errorTitle = "Invalid Entry"
                        # Optionally set a custom prompt message
                        dv.prompt = "Please select from the list"
                        dv.promptTitle = "List Selection"

                        # add the data validation to only the cell next to the current cell
                        cell = openpyxl_ws.cell(row=row, column=column + 1)
                        openpyxl_ws.add_data_validation(dv)
                        dv.add(cell)

                        print("no match")
                        row += 1

            x += 1
    excel_stream = BytesIO()
    wb.save(excel_stream)
    excel_stream.seek(0)  # go to the beginning of the stream

    return Response(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# used
# Endpoint to upload a single image from the url
@app.route("/UrlUpload", methods=["POST"])
def UrlUpload():
    app.logger.info("UrlUpload")
    if request.form["url"] == "":
        imageFile = request.files["file"]
        imagePath = ""
    else:
        imagePath = request.form["url"]
    sku = request.form["sku"]
    sku.replace(" ", "")
    imgNum = request.form["imageNumber"]
    flag = request.form["flag"] == "true"
    remBg = request.form["removeBackground"] == "true"
    imageName = f"{sku}_Img{imgNum}"

    folder_name = datetime.today().strftime("%Y-%m-%d")
    # creates a variable to pass to the html page to display the image and url
    BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{imageName}.jpg"
    server_path = f"public_html/media/L9/{folder_name}/{imageName}.jpg"

    hostname = app.config["HOSTNAME"]
    username = app.config["USERNAME"]
    password = app.config["PASSWORD"]
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    with pysftp.Connection(
        hostname, username=username, password=password, cnopts=cnopts
    ) as sftp:
        print("Connection succesful")
        app.logger.info("Connection succesful")
        if sftp.exists(server_path) and flag == False:
            flag = True
            error = "Duplicate Image. Would you like to overwrite the image?"
            displayImage = (
                f"https://bikewagonmedia.com/media/L9/{folder_name}/{imageName}.jpg"
            )
            data = {
                "error": error,
                "flag": flag,
                "displayImage": displayImage,
            }
            return data
        else:
            with sftp.cd("public_html/media/L9/"):
                if sftp.exists(folder_name):
                    pass
                else:
                    # create new directory at public_html/media/L9/ with the folder_name variable
                    sftp.mkdir(folder_name)
        if imagePath == "":
            # handle the file upload
            image = Image.open(imageFile).convert("RGBA")
            if remBg:
                image_io = fn.removeBackground(image)
            else:
                image_io = fn.process_image(image)

            sftp.putfo(image_io, server_path)
            # close connection
            sftp.close()
            print("Connection closed")
            data = {"displayImage": BikeWagonUrl, "flag": False}
            return data, 200
        else:
            # handle the url upload
            try:
                # open the image from the url
                response = requests.get(imagePath, stream=True)
                # if the user wants to remove background it processes here.
                if remBg:
                    image = Image.open(BytesIO(response.content))
                    image_io = fn.removeBackground(image)

                else:
                    image = Image.open(BytesIO(response.content)).convert("RGBA")
                    # process the image by passing PIL image to the function
                    image_io = fn.process_image(image)
                sftp.putfo(image_io, server_path)

                # close connection
                sftp.close()
                print("Connection closed")
                data = {"displayImage": BikeWagonUrl, "flag": False}

                return data, 200
            except:
                error = "Invalid URL"
                # if the image wouldn't open then the url is invalid
                json = {"error": error}
                app.logger.error(f"Invalid URL: {error}")
                return json


@app.route("/ImageCsv", methods=["GET", "POST"])
@cross_origin(supports_credentials=True)
def ImageCsv():
    if request.method == "GET":
        return "ImageCsv"
    else:
        app.logger.info("ImageCsv - POST")
        totalUploaded = 0

        file = request.files["file"]
        folder = request.files.getlist("file[]")
        df = pd.read_csv(file)
        # if the url doesn't work, keep track of it and remove it from the df
        BrokenUrlDict = {}
        # need to come up with an error catch for columns
        df.columns = map(str.upper, df.columns)
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace(" ", "_")

        # if not folder:
        #     columnList = ["Image 1", "SKU", "Parent SKU", "Parent SKU_Color"]

        #     if all(value in df.columns for value in columnList):
        #         print("All values are present in column names.")
        #     else:
        #         error = "Missing column names. Please make sure Image 1, SKU, Parent SKU, and Parent SKU_Color are present in the csv file."
        #         return error, status.HTTP_400_BAD_REQUEST
        df.dropna(subset=["IMAGE_1"], inplace=True)
        df_copy = df.dropna(axis=1, how="all")
        folder_name = datetime.today().strftime("%Y-%m-%d")
        # maxPictureCount is used to extend the df columns to the right number of images.
        maxImageColCount = 1

        # see how many images columns there are and add one extra to avoid index out of range error
        while f"IMAGE_{maxImageColCount}" in df_copy.columns:
            maxImageColCount += 1
        maxImageColCount -= 1

        if "PARENT_SKU_COLOR" in df.columns:
            uniqueCombo = df["PARENT_SKU_COLOR"].unique()
            columnIdentifier = "PARENT_SKU_COLOR"
            if len(uniqueCombo) == 1:
                error = "There are no values for the Parent SKU Color column. Please make sure there are values in the column. OR remove the header if you want to use SKU as the identifier."
                return (error, status.HTTP_400_BAD_REQUEST)
        else:
            uniqueCombo = df["SKU"].unique()
            columnIdentifier = "SKU"

        # allows you to upload a file or url
        # doesn't require the export sheet. You can export the sourcing sheet

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
                        app.logger.debug(f"Processing combo: {combo}")
                        urlList = ""

                        # x keeps track of the number of images for each parent SKU color combo
                        x = 1
                        # CaDf.append([{"Inventory Number": sku}])
                        dfCombo = df[df[columnIdentifier] == combo]
                        # if a parent_color combo has more than one unique URL in the comboDf we need to handle it differently
                        uniquePath = dfCombo[f"IMAGE_{x}"].unique()
                        # dfCombo.dropna(axis=1, inplace=True)
                        dfCombo.reset_index(drop=True, inplace=True)
                        # print(dfCombo)
                        # error catch: Could also change this to process the filtered df by Child sku and not make the user do it manually
                        # Allows there to be unique urls even if the parent sku combo is the same

                        if len(uniquePath) > 1:
                            # this goes by SKU rather than combo so if there are multiple unique urls for a sku it will process them
                            print(uniquePath)
                            for unique in uniquePath:
                                # reset to the original dfCombo
                                dfCombo = df[df[columnIdentifier] == combo]
                                x = 1
                                # get each line with unique URLS
                                dfCombo = dfCombo[dfCombo[f"IMAGE_{x}"] == unique]
                                dfCombo.reset_index(drop=True, inplace=True)
                                sku = dfCombo["SKU"][0]
                                print(dfCombo["SKU"][0])

                                print(dfCombo[f"IMAGE_{x}"][0])
                                while (
                                    f"IMAGE_{x}" in dfCombo.columns
                                    and dfCombo[f"IMAGE_{x}"].count() > 0
                                ):
                                    # if it is a url
                                    imageUrl = dfCombo[f"IMAGE_{x}"][0]
                                    try:
                                        requests.get(imageUrl, stream=True)
                                        server_path = f"public_html/media/L9/{folder_name}/{sku}_{x}.jpg"

                                        try:
                                            response = requests.get(
                                                imageUrl, stream=True
                                            )
                                            image = Image.open(
                                                BytesIO(response.content)
                                            ).convert("RGBA")
                                            image_io = fn.process_image(image)
                                            sftp.putfo(image_io, server_path)
                                            totalUploaded += 1
                                            app.logger.info(
                                                f"Total images uploaded: {totalUploaded}"
                                            )
                                            BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_{x}.jpg"

                                            # adds a column with the value of the new url to the df
                                            df.loc[
                                                df["SKU"] == sku,
                                                f"Server Image {x}",
                                            ] = BikeWagonUrl

                                            # adds the new column name to the list so we can get all the needed columns later
                                            if f"Server Image {x}" not in columns:
                                                columns.append(f"Server Image {x}")

                                            # adds the url to the urlList variable so we can add it to the csv file for Channal Advisor upload
                                            if urlList == "":
                                                urlList = BikeWagonUrl
                                            else:
                                                urlList = urlList + "," + BikeWagonUrl

                                        except Exception as e:
                                            app.logger.error(f"Error: {str(e)}")
                                            print(f"Error: {str(e)}")
                                            if sku not in BrokenUrlDict:
                                                BrokenUrlDict[sku] = f"IMAGE_{x}"
                                            else:
                                                BrokenUrlDict[sku] += f", IMAGE_{x}"

                                        x += 1

                                    except:
                                        # this will be the image name in the folder that is uploaded
                                        imagePath = dfCombo[f"IMAGE_{x}"][0]

                                        # if the imagePath contains a . split the string and get everything before the .
                                        if "." in imagePath:
                                            fileName = imagePath.split(".")[0]
                                        else:
                                            fileName = imagePath

                                            for file in folder:
                                                if (
                                                    file.filename.endswith(".jpg")
                                                    or file.filename.endswith(".png")
                                                    or file.filename.endswith(".jpeg")
                                                    or file.filename.endswith(".webp")
                                                    or file.filename.endswith(".JPG")
                                                    or file.filename.endswith(".JPEG")
                                                    or file.filename.endswith(".PNG")
                                                    or file.filename.endswith(".WEBP")
                                                ):
                                                    imageName = file.filename.rsplit(
                                                        "/", 1
                                                    )[-1]
                                                    # remove the file extenstion from the imageName
                                                    imageName = imageName.split(".")[0]

                                                    if imageName == fileName:
                                                        imagePath = file
                                        server_path = f"public_html/media/L9/{folder_name}/{sku}_{x}.jpg"
                                        try:
                                            image = Image.open(imagePath).convert(
                                                "RGBA"
                                            )

                                            image_io = fn.process_image(image)

                                            sftp.putfo(image_io, server_path)
                                            totalUploaded += 1
                                            app.logger.info(
                                                f"Total images uploaded: {totalUploaded}"
                                            )
                                            BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_{x}.jpg"
                                            df.loc[
                                                df[columnIdentifier] == sku,
                                                f"Server Image {x}",
                                            ] = BikeWagonUrl
                                            if f"Server Image {x}" not in columns:
                                                columns.append(f"Server Image {x}")
                                            if urlList == "":
                                                urlList = BikeWagonUrl
                                            else:
                                                urlList = urlList + "," + BikeWagonUrl

                                        except Exception as e:
                                            app.logger.warn(
                                                f"Error: {str(e)} -- {imagePath}"
                                            )
                                            print(imagePath)
                                            print(f"Error: {str(e)}")
                                            if sku not in BrokenUrlDict:
                                                BrokenUrlDict[sku] = f"IMAGE_{x}"
                                            else:
                                                BrokenUrlDict[sku] += f", IMAGE_{x}"
                                            print(BrokenUrlDict)

                                        x += 1

                        else:
                            # this process the df using just parent so if all children have the same url it will process them
                            while (
                                f"IMAGE_{x}" in dfCombo.columns
                                and dfCombo[f"IMAGE_{x}"].count() > 0
                            ):
                                ####### I need to fix x and make sure the variable isn't reused####

                                # if it is a url
                                imageUrl = dfCombo[f"IMAGE_{x}"][0]
                                try:
                                    response = requests.get(imageUrl, stream=True)
                                except:
                                    # this is a broken url so we don't get a response on purpose
                                    response = requests.get(
                                        "https://bikewagonmedia.com/BrokenUrl",
                                        stream=True,
                                    )

                                server_path = f"public_html/media/L9/{folder_name}/{combo}_{x}.jpg"
                                app.logger.info(f"{imageUrl} -- {response.status_code}")
                                if response.status_code == 200:
                                    try:
                                        image = Image.open(
                                            BytesIO(response.content)
                                        ).convert("RGBA")
                                        image_io = fn.process_image(image)
                                        sftp.putfo(image_io, server_path)
                                        totalUploaded += 1
                                        app.logger.info(
                                            f"Total images uploaded: {totalUploaded}"
                                        )
                                        BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{combo}_{x}.jpg"
                                        df.loc[
                                            df[columnIdentifier] == combo,
                                            f"Server Image {x}",
                                        ] = BikeWagonUrl
                                        if f"Server Image {x}" not in columns:
                                            columns.append(f"Server Image {x}")
                                        if urlList == "":
                                            urlList = BikeWagonUrl
                                        else:
                                            urlList = urlList + "," + BikeWagonUrl

                                    except Exception as e:
                                        app.logger.error(f"Error: {str(e)}")
                                        print(f"Error: {str(e)}")
                                        print(imageUrl)
                                        if combo not in BrokenUrlDict:
                                            BrokenUrlDict[combo] = f"IMAGE_{x}"
                                        else:
                                            BrokenUrlDict[combo] += f", IMAGE_{x}"
                                        print(BrokenUrlDict)

                                    x += 1

                                else:
                                    # this will be the image name in the folder that is uploaded
                                    imagePath = dfCombo[f"IMAGE_{x}"][0]

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
                                    server_path = f"public_html/media/L9/{folder_name}/{combo}_{x}.jpg"
                                    try:
                                        image = Image.open(imagePath).convert("RGBA")

                                        image_io = fn.process_image(image)

                                        sftp.putfo(image_io, server_path)
                                        totalUploaded += 1
                                        app.logger.info(
                                            f"Total images uploaded: {totalUploaded}"
                                        )
                                        BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{combo}_{x}.jpg"
                                        df.loc[
                                            df[columnIdentifier] == combo,
                                            f"Server Image {x}",
                                        ] = BikeWagonUrl
                                        if f"Server Image {x}" not in columns:
                                            columns.append(f"Server Image {x}")
                                        if urlList == "":
                                            urlList = BikeWagonUrl
                                        else:
                                            urlList = urlList + "," + BikeWagonUrl

                                    except Exception as e:
                                        app.logger.error(f"Error: {str(e)}")
                                        app.logger.error(
                                            f"There was an issue with {imagePath}"
                                        )
                                        print(imagePath)
                                        print(f"Error: {str(e)}")
                                        if combo not in BrokenUrlDict:
                                            BrokenUrlDict[combo] = f"IMAGE_{x}"
                                        else:
                                            BrokenUrlDict[combo] += f", IMAGE_{x}"
                                        print(BrokenUrlDict)
                                    x += 1

                        df.loc[df[columnIdentifier] == combo, "Picture URLs"] = urlList
                except Exception as e:
                    app.logger.error(f"ERROR: {e}")
                    print(f"Error: {str(e)}")
                    error = f"An error occured uploading {combo}. Please check this PARENT_SKU_COLOR and try again."
                    return (error, status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            app.logger.error(f"ERROR: {e}")
            error = f"An error occured connecting to the FTP server. Contact IT"
            print(combo)
            print(f"Error: {str(e)}")
            return (error, status.HTTP_400_BAD_REQUEST)

        app.logger.info("Finished uploading images")

        if "PARENT_SKU" in df.columns:
            columns.extend(
                [
                    "SKU",
                    "PARENT_SKU",
                    "PARENT_SKU_COLOR",
                    "Picture URLs",
                ]
            )
        else:
            columns.extend(
                [
                    "SKU",
                    "Picture URLs",
                ]
            )
        # if there is a video column and it is not empty add video to the df we will return
        if "VIDEO" in df.columns and df["VIDEO"].count() > 0:
            df["Attribute1Name"] = "VideoProduct"
            df.rename(columns={"VIDEO": "Attribute1Value"}, inplace=True)
            columns.extend(["Attribute1Value", "Attribute1Name"])

        columns.extend(["TITLE"])
        ServerImageColumns = []
        x = 0
        while x < maxImageColCount:
            x += 1
            columns.extend([f"IMAGE_{x}"])
            ServerImageColumns.append(f"Server Image {x}")
        try:
            df = df[columns]
        except Exception as e:
            app.logger.error(f"ERROR: {e}")
            error = "The uploaded CSV does not contain the correct columns. Please check for Title and SKU at the minimum. (case matters)"
            return error, status.HTTP_400_BAD_REQUEST

        # drop rows where df doesn't have an image 1 (this will get rid of skus that don't have images)
        df = df.dropna(subset=ServerImageColumns, how="all")

        try:
            df.set_index("SKU", inplace=True)
            dfJson = df.to_json(orient="index")
        except Exception as e:
            app.logger.error(f"ERROR: {e}")
            print(f"Error: {str(e)}")
            error = "The CSV either has a SKU repeated or has extra blank data. Please delete all blank rows and try again."
            return error, status.HTTP_400_BAD_REQUEST

        # create a dictionary using the sku as the key and the Server Image 1 with the url as the value

        # print(response.headers)

        # this will pass the rows as objects
        # return df.to_json(orient="records")
        if BrokenUrlDict == {}:
            ResponseData = {"df": dfJson}

        else:
            ResponseData = {"df": dfJson, "errorDict": BrokenUrlDict}
        return jsonify(ResponseData)


# It is important that the df has the Picture URLs column or else you will just end up with a list of parent skus and the first picture from the child.
@app.route("/downloadTest", methods=["POST"])
def downloadTest():
    downloadWithErrors = request.form["downloadWithErrors"]
    # gets the df formatted in the input format and converts it to Channel Advisor format
    df = request.form["df"]
    df = pd.read_json(df, orient="index")
    folder = request.form["bool"]

    print(df)
    if downloadWithErrors == "true":
        df = df.fillna("")
    else:
        errorDict = request.form["errorDict"]
        errorDict = json.loads(errorDict)
        if errorDict != {}:
            for key in errorDict:
                df = df[df["PARENT_SKU_COLOR"] != key]

    ###### assign parent the first image ########
    ###### add to download part of app ##########
    # if childOnly == "false":
    #     uniqueParent = df["Parent SKU"].unique()
    #     for parent in uniqueParent:
    #         UrlList = ""
    #         parentDf = df.loc[df["Parent SKU"] == parent]
    #         uniqueParentColor = parentDf["Parent SKU_Color"].unique()
    #         for combo in uniqueParentColor:
    #             ComboDf = df.loc[df["Parent SKU_Color"] == combo]
    #             url = ComboDf["Server Image 1"].iloc[0]
    #             if UrlList == "":
    #                 UrlList = url
    #             else:
    #                 UrlList = UrlList + "," + url
    #         df = pd.concat(
    #             [df, pd.DataFrame({"Picture URLs": UrlList}, index=[parent])],
    #         )
    #     print(df)

    # assigns the first image to the parent SKU
    uniqueParent = df["PARENT_SKU"].unique()
    for parent in uniqueParent:
        UrlList = ""
        parentDf = df.loc[df["PARENT_SKU"] == parent]
        uniqueParentColor = parentDf["PARENT_SKU_COLOR"].unique()
        for combo in uniqueParentColor:
            ComboDf = df.loc[df["PARENT_SKU_COLOR"] == combo]
            url = ComboDf["Server Image 1"].iloc[0]
            if UrlList == "":
                UrlList = url
            else:
                UrlList = UrlList + "," + url
        df = pd.concat(
            [df, pd.DataFrame({"Picture URLs": UrlList}, index=[parent])],
        )
    print(df)
    df.dropna(subset=["Picture URLs"], inplace=True)
    columns = ["Picture URLs"]
    if "Attribute1Value" in df.columns:
        columns.extend(["Attribute1Name", "Attribute1Value"])

    df["Labels"] = "BigCommerce"
    ChannelAdvisorDf = df[columns]
    ChannelAdvisorDf.rename_axis("Inventory Number", inplace=True)
    csv = ChannelAdvisorDf.to_csv(index=True)
    date = datetime.now().strftime("%Y-%m-%d")

    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={date}_ImportReady.csv"},
    )


# used for CSV page
@app.route("/DeleteImage", methods=["POST"])
def DeleteImage():
    url = request.form["url"]
    df = request.form["df"]
    df = pd.read_json(df, orient="index")
    print(df.columns)
    # df = df.replace("", pd.NA)

    for x in range(1, 10):
        if url in df[f"Server Image {x}"].values:
            # get the parent color of the row that matches the url so we can update all items with this parent color
            parentColor = df.loc[df[f"Server Image {x}"] == url, "PARENT_SKU_COLOR"][0]
            # clear the urlList from the df
            df.loc[df["PARENT_SKU_COLOR"] == parentColor, "Picture URLs"] = ""

            while f"Server Image {x+1}" in df.columns:
                # pull the row that has the index which is the sku variable above
                df.loc[
                    df["PARENT_SKU_COLOR"] == parentColor, f"Server Image {x}"
                ] = df.loc[
                    df["PARENT_SKU_COLOR"] == parentColor, f"Server Image {x+1}"
                ][
                    0
                ]
                x += 1

            else:
                df.loc[df["PARENT_SKU_COLOR"] == parentColor, f"Server Image {x}"] = ""

            break
    urlList = ""
    x = 1
    print(df.loc[df["PARENT_SKU_COLOR"] == parentColor, f"Server Image {x}"][0])
    while (
        df.loc[df["PARENT_SKU_COLOR"] == parentColor, f"Server Image {x}"][0] != ""
        and df.loc[df["PARENT_SKU_COLOR"] == parentColor, f"Server Image {x}"][0]
        != None
    ):
        print(df.loc[df["PARENT_SKU_COLOR"] == parentColor, f"Server Image {x}"][0])
        if urlList == "":
            urlList = df.loc[
                df["PARENT_SKU_COLOR"] == parentColor, f"Server Image {x}"
            ][0]
            x += 1
        else:
            urlList = (
                urlList
                + ","
                + df.loc[df["PARENT_SKU_COLOR"] == parentColor, f"Server Image {x}"][0]
            )
            x += 1
    print(urlList)
    df.loc[df["PARENT_SKU_COLOR"] == parentColor, "Picture URLs"] = urlList

    index_l9 = url.find("/L9")
    file = url[index_l9:]
    print(file)

    server_path = f"public_html/media{file}"
    hostname = app.config["HOSTNAME"]
    username = app.config["USERNAME"]
    password = app.config["PASSWORD"]

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    try:
        with pysftp.Connection(
            hostname, username=username, password=password, cnopts=cnopts
        ) as sftp:
            sftp.remove(server_path)
            sftp.close()
    except Exception as e:
        app.logger.error(f"ERROR: {e}")
        print(f"Error: {str(e)}")
    dfJson = df.to_json(orient="index")
    return jsonify(dfJson)


# used for single image page
@app.route("/DeleteSingleImage", methods=["POST"])
def DeleteSingleImage():
    sku = request.form["sku"]
    imageNumber = request.form["imageNumber"]
    folder_name = datetime.today().strftime("%Y-%m-%d")

    server_path = f"public_html/media/L9/{folder_name}/{sku}_Img{imageNumber}.jpg"
    hostname = app.config["HOSTNAME"]
    username = app.config["USERNAME"]
    password = app.config["PASSWORD"]

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    try:
        with pysftp.Connection(
            hostname, username=username, password=password, cnopts=cnopts
        ) as sftp:
            sftp.remove(server_path)
            sftp.close()
    except Exception as e:
        app.logger.error(f"Error: {e}")
        print(f"Error: {str(e)}")

    return "success"


# new packageBuilder route
@app.route("/packageBuilder", methods=["POST"])
def packageBuilder():
    imageCount = int(request.form["count"])
    packageType = request.form["type"]
    sku = request.form["sku"]
    flag = request.form["flag"]
    saveAsNew = request.form["saveAsNew"]

    if request.form["mainUrl"] == "":
        skiBoard = request.files["mainFile"]
    else:
        skiBoard = request.form["mainUrl"]

    if imageCount == 1:
        packageImage = fn.skiBuilder(skiBoard)
    elif imageCount == 2:
        if request.form["bootBindingUrl"] == "":
            bootBinding = request.files["bootBindingFile"]
        else:
            bootBinding = request.form["bootBindingUrl"]

        if packageType == "Ski":
            packageImage = fn.twoItemSkiPackageBuilder(skiBoard, bootBinding)
        elif packageType == "Board":
            packageImage = fn.twoItemBoardPackageBuilder(skiBoard, bootBinding)
    elif imageCount == 3:
        if request.form["bootUrl"] == "":
            boot = request.files["bootFile"]
        else:
            boot = request.form["bootUrl"]

        if request.form["bindingUrl"] == "":
            binding = request.files["bindingFile"]
        else:
            binding = request.form["bindingUrl"]
        if packageType == "Ski":
            packageImage = fn.skiPackageBuilder(skiBoard, boot, binding)
        elif packageType == "Board":
            packageImage = fn.boardPackageBuilder(skiBoard, boot, binding)

    image_io = BytesIO()
    packageImage.convert("RGB").save(image_io, "JPEG")

    # Upload the image to the server
    image_io.seek(0)  # Reset the file pointer to the beginning

    imageNumber = 1
    folder_name = datetime.today().strftime("%Y-%m-%d")
    server_path = f"public_html/media/L9/{folder_name}/{sku}_Img{imageNumber}.jpg"
    BikeWagonUrl = (
        f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_Img{imageNumber}.jpg"
    )

    # save packageImage to server
    hostname = app.config["HOSTNAME"]
    username = app.config["USERNAME"]
    password = app.config["PASSWORD"]

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    try:
        with pysftp.Connection(
            hostname, username=username, password=password, cnopts=cnopts
        ) as sftp:
            # if the path exists and flag is flase then we need to tell the user that this is a duplicate.
            # if flag is true then the user already knows it is a duplicate and wants to override it
            if sftp.exists(server_path) and flag == "false":
                flag = True
                error = "Duplicate Image. Would you like to overwrite the image?"
                displayImage = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_Img{imageNumber}.jpg"
                data = {
                    "error": error,
                    "flag": flag,
                    "displayImage": displayImage,
                    "imageNumber": imageNumber,
                }
                return data
            # if the path exists and saveAsNew is true the user wants to add a new image and not override the old one
            # so we need to find the next available image number for that sku
            if sftp.exists(server_path) and saveAsNew == "true":
                while sftp.exists(server_path):
                    imageNumber += 1
                    server_path = (
                        f"public_html/media/L9/{folder_name}/{sku}_Img{imageNumber}.jpg"
                    )
                    BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_Img{imageNumber}.jpg"

            with sftp.cd("public_html/media/L9/"):
                if sftp.exists(folder_name):
                    pass
                else:
                    # create new directory at public_html/media/L9/ with the folder_name variable
                    sftp.mkdir(folder_name)

            sftp.putfo(image_io, server_path)

            # close connection
            sftp.close()
            print("Connection closed")
            data = {
                "displayImage": BikeWagonUrl,
                "flag": False,
                "error": False,
                "imageNumber": imageNumber,
            }
            return data, 200
    except Exception as e:
        print(e)

    return "success"


@app.route("/filePackageBuilder", methods=["POST"])
def filePackageBuilder():
    app.logger.info("filePackageBuilder - POST")
    file = request.files["file"]
    folder = request.files.getlist("file[]")
    df = pd.read_csv(file)
    # if the url doesn't work, keep track of it and remove it from the df
    BrokenUrlDict = {}
    for column in df.columns:
        print(column)

    df.columns = map(str.upper, df.columns)
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace(" ", "_")
    df.dropna(subset=["MAIN_IMAGE_URL"], inplace=True)

    df = df[df["VARIATION_PARENT_SKU"] != "Parent"]
    uniqueCombo = df["VARIATION_PARENT_SKU"].unique()

    for column in df.columns:
        print(column)

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

                    if (
                        comboDf["BOOT_IMAGE_URL"].count() > 0
                        and comboDf["BINDING_IMAGE_URL"].count() > 0
                    ):
                        total = 3
                        skiBoard = comboDf["MAIN_IMAGE_URL"][0]
                        boot = comboDf["BOOT_IMAGE_URL"][0]
                        binding = comboDf["BINDING_IMAGE_URL"][0]
                        if packageType == "Ski":
                            packageImage = fn.skiPackageBuilder(skiBoard, boot, binding)
                        elif packageType == "Board":
                            packageImage = fn.boardPackageBuilder(
                                skiBoard, boot, binding
                            )

                    elif (
                        comboDf["BOOT_IMAGE_URL"].count() > 0
                        and comboDf["BINDING_IMAGE_URL"].count() == 0
                    ):
                        total = 2
                        skiBoard = comboDf["MAIN_IMAGE_URL"][0]
                        boot = comboDf["BOOT_IMAGE_URL"][0]
                        if packageType == "Ski":
                            packageImage = fn.twoItemSkiPackageBuilder(skiBoard, boot)
                        elif packageType == "Board":
                            packageImage = fn.twoItemBoardPackageBuilder(skiBoard, boot)
                    elif (
                        comboDf["BOOT_IMAGE_URL"].count() == 0
                        and comboDf["BINDING_IMAGE_URL"].count() > 0
                    ):
                        total = 2
                        skiBoard = comboDf["MAIN_IMAGE_URL"][0]
                        binding = comboDf["BINDING_IMAGE_URL"][0]
                        if packageType == "Ski":
                            packageImage = fn.twoItemSkiPackageBuilder(
                                skiBoard, binding
                            )
                        elif packageType == "Board":
                            packageImage = fn.twoItemBoardPackageBuilder(
                                skiBoard, binding
                            )

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

                    # add the first image to the urlList that is used to download the csv
                    urlList = BikeWagonUrl

                    if skiBoard.startswith("https://bikewagonmedia.com"):
                        BikeWagonUrl = skiBoard
                    else:
                        server_path = (
                            f"public_html/media/L9/{folder_name}/{sku}_Img2.jpg"
                        )
                        response = requests.get(skiBoard, stream=True)
                        image = Image.open(BytesIO(response.content)).convert("RGBA")
                        image_io = fn.process_image(image)
                        sftp.putfo(image_io, server_path)
                        BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_Img2.jpg"

                    df.loc[
                        df["VARIATION_PARENT_SKU"] == combo,
                        "Server Image 2",
                    ] = BikeWagonUrl

                    urlList = urlList + "," + BikeWagonUrl

                    if total == 3:
                        if boot.startswith("https://bikewagonmedia.com"):
                            BikeWagonUrl = boot
                        else:
                            server_path = (
                                f"public_html/media/L9/{folder_name}/{sku}_Img3.jpg"
                            )
                            response = requests.get(boot, stream=True)
                            image = Image.open(BytesIO(response.content)).convert(
                                "RGBA"
                            )
                            image_io = fn.process_image(image)
                            sftp.putfo(image_io, server_path)
                            BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_Img3.jpg"
                        df.loc[
                            df["VARIATION_PARENT_SKU"] == combo,
                            "Server Image 3",
                        ] = BikeWagonUrl

                        urlList = urlList + "," + BikeWagonUrl

                        if binding.startswith("https://bikewagonmedia.com"):
                            BikeWagonUrl = binding
                        else:
                            server_path = (
                                f"public_html/media/L9/{folder_name}/{sku}_Img4.jpg"
                            )
                            response = requests.get(binding, stream=True)
                            image = Image.open(BytesIO(response.content)).convert(
                                "RGBA"
                            )
                            image_io = fn.process_image(image)
                            sftp.putfo(image_io, server_path)
                            BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_Img4.jpg"
                        df.loc[
                            df["VARIATION_PARENT_SKU"] == combo,
                            "Server Image 4",
                        ] = BikeWagonUrl

                        urlList = urlList + "," + BikeWagonUrl
                    else:
                        if boot != "":
                            if boot.startswith("https://bikewagonmedia.com"):
                                BikeWagonUrl = boot
                            else:
                                server_path = (
                                    f"public_html/media/L9/{folder_name}/{sku}_Img3.jpg"
                                )
                                response = requests.get(boot, stream=True)
                                image = Image.open(BytesIO(response.content)).convert(
                                    "RGBA"
                                )
                                image_io = fn.process_image(image)
                                sftp.putfo(image_io, server_path)
                                BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_Img3.jpg"
                            df.loc[
                                df["VARIATION_PARENT_SKU"] == combo,
                                "Server Image 3",
                            ] = BikeWagonUrl

                            urlList = urlList + "," + BikeWagonUrl

                        elif binding != "":
                            if binding.startswith("https://bikewagonmedia.com"):
                                BikeWagonUrl = binding
                            else:
                                server_path = (
                                    f"public_html/media/L9/{folder_name}/{sku}_Img3.jpg"
                                )
                                response = requests.get(binding, stream=True)
                                image = Image.open(BytesIO(response.content)).convert(
                                    "RGBA"
                                )
                                image_io = fn.process_image(image)
                                sftp.putfo(image_io, server_path)
                                BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_Img3.jpg"
                            df.loc[
                                df["VARIATION_PARENT_SKU"] == combo,
                                "Server Image 3",
                            ] = BikeWagonUrl

                            urlList = urlList + "," + BikeWagonUrl

                    df.loc[
                        df["VARIATION_PARENT_SKU"] == combo, "Picture URLs"
                    ] = urlList
            except Exception as e:
                error = "Error creating package"
                print(e)
                return error, status.HTTP_500_INTERNAL_SERVER_ERROR
    except Exception as e:
        error = "Error connecting to server"
        print(e)
        return error, status.HTTP_500_INTERNAL_SERVER_ERROR

    df = df.rename(columns={"VARIATION_PARENT_SKU": "PARENT_SKU_COLOR"})
    df["PARENT_SKU"] = df["PARENT_SKU_COLOR"]
    df.dropna(subset=["Server Image 1"], inplace=True)

    df.set_index("INVENTORY_NUMBER", inplace=True)
    dfJson = df.to_json(orient="index")
    ResponseData = {"df": dfJson, "errorDict": BrokenUrlDict}
    return ResponseData


if __name__ == "__main__":
    app.run()

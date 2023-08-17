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
import validators
from openpyxl.workbook import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from flask_api import status
from openpyxl.worksheet.datavalidation import DataValidation
import gspread
import logging
pd.options.mode.chained_assignment = None  # default='warn'

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(28)
app.config["HOSTNAME"] = os.environ["FLASK_HOSTNAME"]
app.config["USERNAME"] = os.environ["FLASK_USERNAME"]
app.config["PASSWORD"] = os.environ["FLASK_PASSWORD"]
app.config["GSHEETSKEY"] = os.environ["FLASK_GSHEETS_KEY"]

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

logging.basicConfig(filename='DebugLogs.log', encoding='utf-8', level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
                if (
                    SalesForceDf["Territory Restrictions"][x]
                    == "3 - No Restrictions"
                ):
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
                            cell = NewSheet.cell(
                                row=printRow + 1, column=columnNumber
                            )
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
@cross_origin(supports_credentials=True)
def UrlUpload():
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
    if validators.url(imagePath):
        try:
            # open the image from the url
            response = requests.get(imagePath, stream=True)
        except:
            error = "Invalid URL"
            # if the image wouldn't open then the url is invalid
            return error

        # if the user wants to remove background it processes here.
        if remBg:
            # code to remove background
            BikeWagonUrl = fn.removeBackground(imagePath, imageName)

        else:
            # connect to server
            hostname = app.config["HOSTNAME"]
            username = app.config["USERNAME"]
            password = app.config["PASSWORD"]

            # hostname = os.getenv("hostname")
            # username = os.getenv("username")
            # password = os.getenv("password")

            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None

            server_path = f"public_html/media/L9/{folder_name}/{imageName}.jpg"
            

            try:
                with pysftp.Connection(
                    hostname, username=username, password=password, cnopts=cnopts
                ) as sftp:
                    print("Connection succesful")
                    logger.info("Connection succesful")
                    if sftp.exists(server_path) and flag == False:
                        flag = True
                        error = (
                            "Duplicate Image. Would you like to overwrite the image?"
                        )
                        displayImage = f"https://bikewagonmedia.com/media/L9/{folder_name}/{imageName}.jpg"
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

                        image = Image.open(BytesIO(response.content)).convert("RGBA")

                        # process the image by passing PIL image to the function
                        image_io = fn.process_image(image)
                        sftp.putfo(image_io, server_path)

                        # close connection
                        sftp.close()
                        print("Connection closed")

            except Exception as e:
                logger.error(f"Error connecting to server: {e}")
                print(e)
                error = "Error connecting to server"
                return error

        data = {"displayImage": BikeWagonUrl, "flag": False}

        return data, 200
    else:
        if remBg:
            # code to remove background
            BikeWagonUrl = fn.removeBackground(imagePath, imageName)

        else:
            # connect to server
            hostname = app.config["HOSTNAME"]
            username = app.config["USERNAME"]
            password = app.config["PASSWORD"]
            # hostname = os.getenv("hostname")
            # username = os.getenv("username")
            # password = os.getenv("password")

            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None

            server_path = f"public_html/media/L9/{folder_name}/{imageName}.jpg"

            try:
                with pysftp.Connection(
                    hostname, username=username, password=password, cnopts=cnopts
                ) as sftp:
                    print("Connection succesful")
                    logger.info("Connection succesful")
                    if sftp.exists(server_path) and flag == False:
                        flag = True
                        error = (
                            "Duplicate Image. Would you like to overwrite the image?"
                        )
                        displayImage = f"https://bikewagonmedia.com/media/L9/{folder_name}/{imageName}.jpg"
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

                        image = Image.open(imagePath).convert("RGBA")

                        image_io = fn.process_image(image)

                        sftp.putfo(image_io, server_path)

                        # close connection
                        sftp.close()
                        print("Connection closed")
                        data = {"displayImage": BikeWagonUrl, "flag": False}
                        return data, 200

            except Exception as e:
                print(f"Error: {str(e)}")
                return "Error", 400

# used
@app.route("/ImageCsvTest", methods=["GET", "POST"])
@cross_origin(supports_credentials=True)
def ImageCsvTest():
    if request.method == "GET":
        return "Success"
    else:
        # keeps the program running
        
        # Do something that takes a long time
        file = request.files["file"]
        folder = request.files.getlist("file[]")
        df = pd.read_csv(file)
        # if the url doesn't work, keep track of it and remove it from the df
        BrokenUrlDict = {}

        if not folder:
            columnList = ["Image 1", "SKU", "Parent SKU", "Parent SKU_Color"]

            if all(value in df.columns for value in columnList):
                print("All values are present in column names.")
            else:
                error = "Missing column names. Please make sure Image 1, SKU, Parent SKU, and Parent SKU_Color are present in the csv file."
                return error, status.HTTP_400_BAD_REQUEST
        df.dropna(subset=["Image 1"], inplace=True)
        df_copy = df.dropna(axis=1, how="all")
        folder_name = datetime.today().strftime("%Y-%m-%d")
        # maxPictureCount is used to extend the df columns to the right number of images.
        maxImageColCount = 1

        # see how many images columns there are and add one extra to avoid index out of range error
        while f"Image {maxImageColCount}" in df_copy.columns:
            maxImageColCount += 1
        maxImageColCount -= 1

        # allows you to upload a file or url
        # doesn't require the export sheet. You can export the sourcing sheet
        # CaDf = pd.DataFrame(columns=["Inventory Number", "Picture URLs"])
        uniqueParentColor = df["Parent SKU_Color"].unique()
        hostname = app.config["HOSTNAME"]
        username = app.config["USERNAME"]
        password = app.config["PASSWORD"]
        # hostname = os.getenv("hostname")
        # username = os.getenv("username")
        # password = os.getenv("password")
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
                with sftp.cd("public_html/media/L9/"):
                    if sftp.exists(folder_name) == False:
                        # create new directory at public_html/media/L9/ with the folder_name variable
                        sftp.mkdir(folder_name)

                try:
                    # getting the uniqueSku problem is you download images multiple times
                    for combo in uniqueParentColor:
                        urlList = ""

                        # x keeps track of the number of images for each parent SKU color combo
                        x = 1
                        # CaDf.append([{"Inventory Number": sku}])
                        dfCombo = df[df["Parent SKU_Color"] == combo]
                        # if a parent_color combo has more than one unique URL in the comboDf we need to handle it differently
                        uniquePath = dfCombo[f"Image {x}"].unique()
                        # dfCombo.dropna(axis=1, inplace=True)
                        dfCombo.reset_index(drop=True, inplace=True)
                        # print(dfCombo)
                        # error catch: Could also change this to process the filtered df by Child sku and not make the user do it manually
                        # Allows there to be unique urls even if the parent sku combo is the same

                        if len(uniquePath) > 1:
                            print(uniquePath)
                            for unique in uniquePath:
                                # reset to the original dfCombo
                                dfCombo = df[df["Parent SKU_Color"] == combo]
                                x = 1
                                # get each line with unique URLS
                                dfCombo = dfCombo[dfCombo[f"Image {x}"] == unique]
                                dfCombo.reset_index(drop=True, inplace=True)
                                sku = dfCombo["SKU"][0]
                                print(dfCombo["SKU"][0])

                                print(dfCombo[f"Image {x}"][0])
                                while dfCombo[f"Image {x}"].count() > 0:
                                    # if it is a url
                                    imageUrl = dfCombo[f"Image {x}"][0]
                                    if validators.url(imageUrl):
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
                                            BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_{x}.jpg"
                                            df.loc[
                                                df["SKU"] == sku,
                                                f"Server Image {x}",
                                            ] = BikeWagonUrl
                                            if f"Server Image {x}" not in columns:
                                                columns.append(f"Server Image {x}")
                                            if urlList == "":
                                                urlList = BikeWagonUrl
                                            else:
                                                urlList = (
                                                    urlList + "," + BikeWagonUrl
                                                )

                                        except Exception as e:
                                            print(f"Error: {str(e)}")
                                            if sku not in BrokenUrlDict:
                                                BrokenUrlDict[sku] = f"Image {x}"
                                            else:
                                                BrokenUrlDict[sku] += f", Image {x}"

                                        x += 1

                                    else:
                                        # if folder is an empty list no images were uploaded and there should be full file paths in the cell for the image
                                        if folder == []:
                                            imagePath = dfCombo[f"Image {x}"][0]

                                        # if folder is not an empty list then there should just be a file name
                                        # in the cell for the image that we will match to an image that is in the uploaded folder
                                        else:
                                            fileName = (
                                                f"{dfCombo[f'Image {x}'][0]}.JPG"
                                            )
                                            for file in folder:
                                                if (
                                                    file.filename.endswith(".jpg")
                                                    or file.filename.endswith(
                                                        ".png"
                                                    )
                                                    or file.filename.endswith(
                                                        ".jpeg"
                                                    )
                                                    or file.filename.endswith(
                                                        ".webp"
                                                    )
                                                    or file.filename.endswith(
                                                        ".JPG"
                                                    )
                                                    or file.filename.endswith(
                                                        ".JPEG"
                                                    )
                                                    or file.filename.endswith(
                                                        ".PNG"
                                                    )
                                                    or file.filename.endswith(
                                                        ".WEBP"
                                                    )
                                                ):
                                                    imageName = (
                                                        file.filename.rsplit(
                                                            "/", 1
                                                        )[-1]
                                                    )

                                                    if imageName == fileName:
                                                        imagePath = file
                                        server_path = f"public_html/media/L9/{folder_name}/{sku}_{x}.jpg"
                                        try:
                                            image = Image.open(imagePath).convert(
                                                "RGBA"
                                            )

                                            image_io = fn.process_image(image)

                                            sftp.putfo(image_io, server_path)
                                            BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{sku}_{x}.jpg"
                                            df.loc[
                                                df["Parent SKU_Color"] == sku,
                                                f"Server Image {x}",
                                            ] = BikeWagonUrl
                                            if f"Server Image {x}" not in columns:
                                                columns.append(f"Server Image {x}")
                                            if urlList == "":
                                                urlList = BikeWagonUrl
                                            else:
                                                urlList = (
                                                    urlList + "," + BikeWagonUrl
                                                )

                                        except Exception as e:
                                            print(imagePath)
                                            print(f"Error: {str(e)}")
                                            if sku not in BrokenUrlDict:
                                                BrokenUrlDict[sku] = f"Image {x}"
                                            else:
                                                BrokenUrlDict[sku] += f", Image {x}"
                                            print(BrokenUrlDict)

                                        x += 1
                        else:
                            while dfCombo[f"Image {x}"].count() > 0:
                                ####### I need to fix x and make sure the variable isn't reused####

                                # if it is a url
                                imageUrl = dfCombo[f"Image {x}"][0]
                                if validators.url(imageUrl):
                                    requests.get(imageUrl, stream=True)
                                    server_path = f"public_html/media/L9/{folder_name}/{combo}_{x}.jpg"

                                    try:
                                        response = requests.get(
                                            imageUrl, stream=True
                                        )
                                        image = Image.open(
                                            BytesIO(response.content)
                                        ).convert("RGBA")
                                        image_io = fn.process_image(image)
                                        sftp.putfo(image_io, server_path)
                                        BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{combo}_{x}.jpg"
                                        df.loc[
                                            df["Parent SKU_Color"] == combo,
                                            f"Server Image {x}",
                                        ] = BikeWagonUrl
                                        if f"Server Image {x}" not in columns:
                                            columns.append(f"Server Image {x}")
                                        if urlList == "":
                                            urlList = BikeWagonUrl
                                        else:
                                            urlList = urlList + "," + BikeWagonUrl

                                    except Exception as e:
                                        print(f"Error: {str(e)}")
                                        print(imageUrl)
                                        if combo not in BrokenUrlDict:
                                            BrokenUrlDict[combo] = f"Image {x}"
                                        else:
                                            BrokenUrlDict[combo] += f", Image {x}"
                                        print(BrokenUrlDict)

                                    x += 1

                                else:
                                    # if folder is an empty list no images were uploaded and there should be full file paths in the cell for the image
                                    if folder == []:
                                        imagePath = dfCombo[f"Image {x}"][0]

                                    # if folder is not an empty list then there should just be a file name
                                    # in the cell for the image that we will match to an image that is in the uploaded folder
                                    else:
                                        fileName = f"{dfCombo[f'Image {x}'][0]}.JPG"
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

                                                if imageName == fileName:
                                                    imagePath = file
                                    server_path = f"public_html/media/L9/{folder_name}/{combo}_{x}.jpg"
                                    try:
                                        image = Image.open(imagePath).convert(
                                            "RGBA"
                                        )

                                        image_io = fn.process_image(image)

                                        sftp.putfo(image_io, server_path)
                                        BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{combo}_{x}.jpg"
                                        df.loc[
                                            df["Parent SKU_Color"] == combo,
                                            f"Server Image {x}",
                                        ] = BikeWagonUrl
                                        if f"Server Image {x}" not in columns:
                                            columns.append(f"Server Image {x}")
                                        if urlList == "":
                                            urlList = BikeWagonUrl
                                        else:
                                            urlList = urlList + "," + BikeWagonUrl

                                    except Exception as e:
                                        print(imagePath)
                                        print(f"Error: {str(e)}")
                                        if combo not in BrokenUrlDict:
                                            BrokenUrlDict[combo] = f"Image {x}"
                                        else:
                                            BrokenUrlDict[combo] += f", Image {x}"
                                        print(BrokenUrlDict)
                                    x += 1

                        df.loc[
                            df["Parent SKU_Color"] == combo, "Picture URLs"
                        ] = urlList
                except Exception as e:
                    print(f"Error: {str(e)}")
                    error = f"An error occured uploading {combo}. Please check this Parent SKU_color and try again."
                    return (error, status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            error = f"An error occured connecting to the FTP server. Contact IT"
            print(combo)
            print(f"Error: {str(e)}")
            return (error, status.HTTP_400_BAD_REQUEST)

        # if folder is empty then we know the sheet has parents
        if folder == []:
            columns.extend(
                ["SKU", "Parent SKU", "Parent SKU_Color", "Picture URLs"]
            )
        # if folder is not empty then we know the sheet only has children.
        else:
            columns.extend(
                [
                    "SKU",
                    "Picture URLs",
                ]
            )
        # if there is a video column and it is not empty add video to the df we will return
        if "Video" in df.columns and df["Video"].count() > 0:
            df["Attribute1Name"] = "VideoProduct"
            columns.extend(["Video", "Attribute1Name"])
        columns.extend(["Title"])
        ServerImageColumns = []
        x = 0
        while x < maxImageColCount:
            x += 1
            columns.extend([f"Image {x}"])
            ServerImageColumns.append(f"Server Image {x}")
        df = df[columns]

        # drop rows where df doesn't have an image 1 (this will get rid of skus that don't have images)
        df = df.dropna(subset=ServerImageColumns, how="all")
        if "Video" in df.columns:
            df.rename(columns={"Video": "Attribute1Value"}, inplace=True)
        # rename video column to VideoProduct
        try:
            df.set_index("SKU", inplace=True)
            dfJson = df.to_json(orient="index")
        except Exception as e:
            error = "The CSV either has a SKU repeated or has extra blank data. Please delete all blank rows and try again."
            return error, status.HTTP_400_BAD_REQUEST

        # create a dictionary using the sku as the key and the Server Image 1 with the url as the value

        # print(response.headers)

        # this will pass the rows as objects
        # return df.to_json(orient="records")

        ResponseData = {"df": dfJson, "errorDict": BrokenUrlDict}
        print(BrokenUrlDict)
        return jsonify(ResponseData)


# used
@app.route("/downloadTest", methods=["POST"])
def downloadTest():
    downloadWithErrors = request.form["downloadWithErrors"]
    # gets the df formatted in the input format and converts it to Channel Advisor format
    df = request.form["df"]
    df = pd.read_json(df, orient="index")
    childOnly = request.form["bool"]
    print(df)
    if downloadWithErrors == "true":
        df = df.fillna("")
    else:
        errorDict = request.form["errorDict"]
        errorDict = json.loads(errorDict)
        if errorDict != {}:
            for key in errorDict:
                df = df[df["Parent SKU_Color"] != key]

    ###### assign parent the first image ########
    ###### add to download part of app ##########
    if childOnly == "false":
        uniqueParent = df["Parent SKU"].unique()
        for parent in uniqueParent:
            UrlList = ""
            parentDf = df.loc[df["Parent SKU"] == parent]
            uniqueParentColor = parentDf["Parent SKU_Color"].unique()
            for combo in uniqueParentColor:
                ComboDf = df.loc[df["Parent SKU_Color"] == combo]
                url = ComboDf["Server Image 1"].iloc[0]
                if UrlList == "":
                    UrlList = url
                else:
                    UrlList = UrlList + "," + url
            df = pd.concat(
                [df, pd.DataFrame({"Picture URLs": UrlList}, index=[parent])],
            )
        print(df)

    columns = ["Picture URLs"]
    if "Attribute1Value" in df.columns:
        columns.extend(["Attribute1Name", "Attribute1Value"])
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
            parentColor = df.loc[df[f"Server Image {x}"] == url, "Parent SKU_Color"][0]
            # clear the urlList from the df
            df.loc[df["Parent SKU_Color"] == parentColor, "Picture URLs"] = ""

            while f"Server Image {x+1}" in df.columns:
                # pull the row that has the index which is the sku variable above
                df.loc[
                    df["Parent SKU_Color"] == parentColor, f"Server Image {x}"
                ] = df.loc[
                    df["Parent SKU_Color"] == parentColor, f"Server Image {x+1}"
                ][
                    0
                ]
                x += 1

            else:
                df.loc[df["Parent SKU_Color"] == parentColor, f"Server Image {x}"] = ""

            break
    urlList = ""
    x = 1
    print(df.loc[df["Parent SKU_Color"] == parentColor, f"Server Image {x}"][0])
    while (
        df.loc[df["Parent SKU_Color"] == parentColor, f"Server Image {x}"][0] != ""
        and df.loc[df["Parent SKU_Color"] == parentColor, f"Server Image {x}"][0]
        != None
    ):
        print(df.loc[df["Parent SKU_Color"] == parentColor, f"Server Image {x}"][0])
        if urlList == "":
            urlList = df.loc[
                df["Parent SKU_Color"] == parentColor, f"Server Image {x}"
            ][0]
            x += 1
        else:
            urlList = (
                urlList
                + ","
                + df.loc[df["Parent SKU_Color"] == parentColor, f"Server Image {x}"][0]
            )
            x += 1
    print(urlList)
    df.loc[df["Parent SKU_Color"] == parentColor, "Picture URLs"] = urlList

    index_l9 = url.find("/L9")
    file = url[index_l9:]
    print(file)

    server_path = f"public_html/media{file}"
    hostname = app.config["HOSTNAME"]
    username = app.config["USERNAME"]
    password = app.config["PASSWORD"]
    # hostname = os.getenv("hostname")
    # username = os.getenv("username")
    # password = os.getenv("password")

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    try:
        with pysftp.Connection(
            hostname, username=username, password=password, cnopts=cnopts
        ) as sftp:
            sftp.remove(server_path)
            sftp.close()
    except Exception as e:
        print(f"Error: {str(e)}")
    dfJson = df.to_json(orient="index")
    return jsonify(dfJson)

#used for single image page
@app.route("/DeleteSingleImage", methods=["POST"])
def DeleteSingleImage():
    sku = request.form["sku"]
    imageNumber = request.form["imageNumber"]
    folder_name = datetime.today().strftime("%Y-%m-%d")

    server_path = f"public_html/media/L9/{folder_name}/{sku}_{imageNumber}.jpg"
    hostname = app.config["HOSTNAME"]
    username = app.config["USERNAME"]
    password = app.config["PASSWORD"]
    # hostname = os.getenv("hostname")
    # username = os.getenv("username")
    # password = os.getenv("password")

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    try:
        with pysftp.Connection(
            hostname, username=username, password=password, cnopts=cnopts
        ) as sftp:
            sftp.remove(server_path)
            sftp.close()
    except Exception as e:
        print(f"Error: {str(e)}")
    
    return "success"

if __name__ == "__main__":
    app.run()

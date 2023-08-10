# from __main__ import app
# from flask import request, jsonify, Blueprint
# import pandas as pd
# from flask_cors import cross_origin
# from datetime import datetime
# import requests
# import pysftp
# from datetime import datetime
# from io import BytesIO
# import credentials
# import functions as fn
# from PIL import Image
# import validators

# ImageSourcing = Blueprint("ImageSourcing", __name__, template_folder="templates")


# @ImageSourcing.route("/ImageCsvTest", methods=["GET", "POST"])
# @cross_origin(supports_credentials=True)
# def ImageCsvTest():
#     if request.method == "GET":
#         return "Success"
#     else:
#         file = request.files["file"]
#         folder = request.files.getlist("file[]")
#         df = pd.read_csv(file)
#         # df = df[df["Image Title"].notna()]
#         # unique_image = df["Image Title"].unique()
#         df.dropna(subset=["Image 1"], inplace=True)
#         print(df)
#         folder_name = datetime.today().strftime("%Y-%m-%d")

#         # allows you to upload a file or url
#         # doesn't require the export sheet. You can export the sourcing sheet
#         CaDf = pd.DataFrame(columns=["Inventory Number", "Picture URLs"])
#         uniqueParentColor = df["Parent SKU_Color"].unique()
#         hostname = credentials.hostname
#         username = credentials.username
#         password = credentials.password
#         columns = []

#         cnopts = pysftp.CnOpts()
#         cnopts.hostkeys = None

#         try:
#             with pysftp.Connection(
#                 hostname,
#                 username=username,
#                 password=password,
#                 cnopts=cnopts,
#             ) as sftp:
#                 with sftp.cd("public_html/media/L9/"):
#                     if sftp.exists(folder_name) == False:
#                         # create new directory at public_html/media/L9/ with the folder_name variable
#                         sftp.mkdir(folder_name)

#                 # getting the uniqueSku problem is you download images multiple times
#                 for combo in uniqueParentColor:
#                     urlList = ""
#                     x = 1
#                     # CaDf.append([{"Inventory Number": sku}])
#                     dfCombo = df[df["Parent SKU_Color"] == combo]
#                     # dfCombo.dropna(axis=1, inplace=True)
#                     dfCombo.reset_index(drop=True, inplace=True)
#                     print(dfCombo)
#                     while dfCombo[f"Image {x}"].count() > 0:
#                         print(dfCombo[f"Image {x}"].count())
#                         # if it is a url
#                         url = dfCombo[f"Image {x}"][0]

#                         if validators.url(url):
#                             imageUrl = dfCombo[f"Image {x}"][0]
#                             requests.get(imageUrl, stream=True)
#                             server_path = (
#                                 f"public_html/media/L9/{folder_name}/{combo}_{x}.jpg"
#                             )

#                             # if the url doesn't work, keep track of it and remove it from the df
#                             BrokenUrlList = []

#                             # get the image from the url
#                             # for imageName in unique_image:
#                             #     # get the img_name associated with the image
#                             #     imageUrl = df[df["Image Title"] == imageName][
#                             #         "Image Url"
#                             #     ].values[0]
#                             #

#                             #     # create a path to the image and add it to the df
#                             #     df.loc[
#                             #         df["Image Title"] == imageName, "Server URL"
#                             #     ] = f"https://bikewagonmedia.com/media/L9/{folder_name}/{imageName}.jpg"

#                             try:
#                                 response = requests.get(imageUrl, stream=True)
#                                 image = Image.open(BytesIO(response.content)).convert(
#                                     "RGBA"
#                                 )
#                                 image_io = fn.process_image(image)
#                                 sftp.putfo(image_io, server_path)

#                             except Exception as e:
#                                 print(f"Error: {str(e)}")
#                                 BrokenUrlList.append(imageUrl)
#                                 # df = df[df["Image Url"] != imageUrl]
#                                 # print(len(df))

#                             BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{combo}_{x}.jpg"
#                             df.loc[
#                                 df["Parent SKU_Color"] == combo, f"Server Image {x}"
#                             ] = BikeWagonUrl
#                             if f"Server Image {x}" not in columns:
#                                 columns.append(f"Server Image {x}")
#                             if urlList == "":
#                                 urlList = BikeWagonUrl
#                             else:
#                                 urlList = urlList + "," + BikeWagonUrl
#                             x += 1

#                         else:
#                             # code for downloading from file
#                             fileName = dfCombo[f"Image {x}"][0]
#                             for file in folder:
#                                 if (
#                                     file.filename.endswith(".jpg")
#                                     or file.filename.endswith(".png")
#                                     or file.filename.endswith(".jpeg")
#                                     or file.filename.endswith(".webp")
#                                 ):
#                                     imageName = file.filename.rsplit("/", 1)[-1]
#                                     if imageName == fileName:
#                                         server_path = f"public_html/media/L9/{folder_name}/{combo}_{x}.jpg"
#                                         try:
#                                             image = Image.open(file).convert("RGBA")

#                                             image_io = fn.process_image(image)

#                                             sftp.putfo(image_io, server_path)

#                                         except Exception as e:
#                                             print(f"Error: {str(e)}")

#                                         BikeWagonUrl = f"https://bikewagonmedia.com/media/L9/{folder_name}/{combo}_{x}.jpg"
#                                         df.loc[
#                                             df["Parent SKU_Color"] == combo,
#                                             f"Server Image {x}",
#                                         ] = BikeWagonUrl
#                                         if f"Server Image {x}" not in columns:
#                                             columns.append(f"Server Image {x}")
#                                         if urlList == "":
#                                             urlList = BikeWagonUrl
#                                         else:
#                                             urlList = urlList + "," + BikeWagonUrl

#                                         x += 1

#                     print(urlList)
#                     df.loc[df["Parent SKU_Color"] == combo, "Picture URLs"] = urlList
#                     print(df["Picture URLs"])
#         except Exception as e:
#             print(f"Error: {str(e)}")

#         ###### assign parent the first image ########
#         ###### add to download part of app ##########
#         # uniqueParent = df["Variation Parent SKU"].unique()

#         # for parent in uniqueParent:
#         #     UrlList = ""
#         #     parentDf = df.loc[df["Parent SKU"] == parent]
#         #     uniqueParentColor = parentDf["Parent SKU_Color"].unique()
#         #     for combo in uniqueParentColor:
#         #         ComboDf = df.loc[df["Parent SKU_Color"] == combo]
#         #         url = ComboDf["Image 1"].iloc[0]
#         #         if UrlList == "":
#         #             UrlList = url
#         #         else:
#         #             UrlList = UrlList + "," + url
#         #     CaDf.append([{"Inventory Number": parent, "Picture URLs": UrlList}])

#         # if the url doesn't work, keep track of it and remove it from the df

#         # dict = fn.CreateDict(df)
#         columns.extend(
#             [
#                 "SKU",
#                 "Parent SKU",
#                 "Parent SKU_Color",
#                 "Image 1",
#                 "Image 2",
#                 "Image 3",
#                 "Image 4",
#                 "Image 5",
#                 "Image 6",
#                 "Image 7",
#                 "Image 8",
#                 "Image 9",
#                 "Picture URLs",
#             ]
#         )
#         df = df[columns]
#         df_copy = df.copy()
#         df.set_index("SKU", inplace=True)

#         dfJson = df.to_json(orient="index")
#         # create a dictionary using the sku as the key and the Server Image 1 with the url as the value

#         print(dfJson)
#         # print(response.headers)

#         # this will pass the rows as objects
#         # return df.to_json(orient="records")

#         # Test = {"DisplayData": dict, "df": dfJson}
#         return jsonify(dfJson)

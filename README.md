# ListingBackend
A python flask API thats primary function is to edit and upload product images to a internal server where they can be hosted. The user can upload a CSV with 
product SKUs and urls or filenames and all the images are uploaded to the server for Level Nine Sports. A Dataframe is returned to the user with the new url 
and is linked to the SKU recieved. The user can then download this Dataframe as a CSV and upload it to the product management system and the photos will go 
live on the website. Additionally there is some spreadsheet manipulation/process automation as well as some image manipulation to automate the 
process of building product images for packages. This application allowed Level Nine to save ~$50,000 annually. I deployed and maintain this API on a DigitalOcean droplet and it integrates with an internal react app that I also developed.
![image 1](https://github.com/wilverine7/ListingBackend/blob/readme/images/image1.png?raw=true "Photo Upload Page)


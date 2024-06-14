from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import logging
import pymongo

logging.basicConfig(filename="scrapper.log", level=logging.INFO)

app = Flask(__name__)
CORS(app)  # Enable CORS if needed

@app.route("/", methods=['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = urlopen(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.findAll("div", {"class": "cPHDOP col-12-12"})
            logging.info(f"Number of bigboxes found: {len(bigboxes)}")
            if len(bigboxes) < 3:
                logging.info("Not enough bigboxes found.")
                return "No products found."

            del bigboxes[0:2]
            if len(bigboxes) == 0:
                logging.info("No product box found after deleting first 3 elements.")
                return "No product box found."

            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            prodRes = requests.get(productLink)
            prodRes.encoding = 'utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            commentboxes = prod_html.find_all('div', {'class': "RcXBOT"})

            if not commentboxes:
                logging.info("No comment boxes found.")
                return "No reviews found."

            reviews = []
            for commentbox in commentboxes:
                try:
                    name = commentbox.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                except:
                    name = 'No Name'
                    logging.info("Name not found")

                try:
                    rating = commentbox.div.div.div.div.text
                except:
                    rating = 'No Rating'
                    logging.info("Rating not found")

                try:
                    commentHead = commentbox.div.div.div.p.text
                except:
                    commentHead = 'No Comment Heading'
                    logging.info("Comment Heading not found")

                try:
                    comtag = commentbox.div.div.find_all('div', {'class': ''})
                    custComment = comtag[0].div.text
                except Exception as e:
                    custComment = 'No Comment'
                    logging.info(e)

                mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                          "Comment": custComment}
                reviews.append(mydict)

            logging.info("log my final result {}".format(reviews))
            uri = "mongodb+srv://harshsingh9222:ranjana526@cluster0.lruqqfb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

            # Create a new client and connect to the server
            client =pymongo.MongoClient(uri)
            db=client['review_scrap']
            review_col=db['review_scrap_data']
            review_col.insert_many(reviews)

            return render_template('result.html', reviews=reviews)
        except Exception as e:
            logging.info(e)
            return 'Something went wrong. Please try again.'
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

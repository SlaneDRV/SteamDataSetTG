## Project: Application for managing wishlist of games on Steam

### Project Team:
- Dzmitry Revutski
- Anton Sasnouski

### Used Technologies:
- Python 3.12
- Telegram Bot API
- Steam Web API

### Project Description:
Our application allows users to search for games available on the Steam platform and add them to their wishlist. Users can view detailed information about games, such as descriptions, ratings, tags, available languages, etc. Additionally, the application enables exporting and importing wishlists in various formats.

### Example questions that can be answered using the application:
1. Which games on the Steam platform match a given search query?
2. What are the detailed information about a particular game, such as ratings, descriptions, available languages?
3. What games are on my wishlist?
4. What games category I play more often?
5. How much costs games from my wishlist at others countries?

## IDE Environment Configuration:
To run the source code, it is recommended to use an environment with Python 3.12 or newer. Install the required libraries listed in the requirements.txt file. 

### Data Sets
Download three json files(actual on 16.06.2024) from the link and add it to package JSON which at the package SteamApi.

Link to json files: https://drive.google.com/drive/folders/1aG1_BkECnypXUDVRk91XYxi7HSUXs3f1?usp=sharing

### Telegram Bot token
Create your own Telegram Bot token and add it to config.py as a TOKEN.

### Dockerisation
To dockerize your Telegram bot for deployment, navigate to the project directory in the terminal and use the following command: docker-compose up --build

Telegram Bot token: https://youtu.be/aNmRNjME6mE?si=ViYQa2Tq7IIO1m_C

### Sources of Used Data:
- Steam Web API: https://developer.valvesoftware.com/wiki/Steam_Web_API

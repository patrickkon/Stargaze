FROM node:12

WORKDIR /usr/src/app
COPY package*.json ./
RUN npm i
RUN npm i express-fileupload
COPY . .

EXPOSE 80
CMD ["node", "server.js"]
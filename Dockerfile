FROM movesrwth/stormpy:1.7.0
RUN mkdir /opt/gridstorm
WORKDIR /opt/gridstorm

RUN apt-get install -y ffmpeg

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python setup.py install
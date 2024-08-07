FROM python:latest
COPY entrypoint.py /entrypoint.py
COPY .config/requirements.in requirements.txt
ENTRYPOINT ["python3", "/entrypoint.py"]
RUN pip3 install -r requirements.txt

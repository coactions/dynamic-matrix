FROM python:latest
COPY entrypoint.py /entrypoint.py
ENTRYPOINT ["python3", "/entrypoint.py"]
RUN pip3 install actions-toolkit

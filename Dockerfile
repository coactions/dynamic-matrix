FROM python:latest
COPY entrypoint.py /entrypoint.py
ENTRYPOINT ["/entrypoint.py"]
RUN pip3 install actions-toolkit

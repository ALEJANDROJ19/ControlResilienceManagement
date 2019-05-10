FROM python:3
ADD . /Policies
WORKDIR /Policies
RUN bash -c "pip install -r requirements.txt"

EXPOSE 46050

#ENV isLeader=False
#ENV DEBUG=False
#ENV MF2C=True

CMD ["python", "-u", "main.py"]
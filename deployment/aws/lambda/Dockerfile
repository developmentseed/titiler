FROM public.ecr.aws/lambda/python:3.8

RUN pip install titiler.application mangum>=0.10.0

COPY lambda/handler.py ${LAMBDA_TASK_ROOT}/

CMD ["handler.handler"]

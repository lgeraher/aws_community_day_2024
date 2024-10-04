# Use the official AWS Lambda Python 3.12 base image
FROM public.ecr.aws/lambda/python:3.12

# Set the working directory in the container
WORKDIR /var/task

# Copy the current directory contents into the container at /var/task
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Command to run the Lambda function when the container starts
# This entry point is specific for AWS Lambda, you don't need to specify a handler here
CMD ["consumer.lambda_handler"]

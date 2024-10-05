# Use the official AWS Lambda Python 3.12 base image
FROM public.ecr.aws/lambda/python:3.12

# Set the working directory
WORKDIR /var/task

# Copy the application code and requirements file
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Command to run the Lambda function
CMD ["consumer.lambda_handler"]
LAMBDA_NAMES = producer processor final pdf_listener
ENDPOINT = --endpoint-url=http://localhost:4566
ROLE_ARN = arn:aws:iam::000000000000:role/lambda-role
AWS_OPTS = --no-cli-pager --cli-read-timeout 0

# Dependencies for each Lambda function
pdf_listener_deps = PyPDF2

deps:
	@echo "📦 Installing dependencies..."
	@if [ -n "$(pdf_listener_deps)" ]; then \
		echo "Installing dependencies for pdf_listener..."; \
		rm -rf lambda/pdf_listener/package lambda/pdf_listener/venv; \
		python3 -m venv lambda/pdf_listener/venv; \
		. lambda/pdf_listener/venv/bin/activate && \
		pip install $(pdf_listener_deps) --upgrade && \
		mkdir -p lambda/pdf_listener/package && \
		pip install $(pdf_listener_deps) -t lambda/pdf_listener/package --upgrade; \
		deactivate; \
	fi
	@echo "✅ Dependencies installed."

zip: deps
	@echo "🔧 Zipping Lambda functions..."
	@for fn in $(LAMBDA_NAMES); do \
		echo "Zipping $$fn..."; \
		if [ "$$fn" = "pdf_listener" ]; then \
			rm -f lambda/$$fn/function.zip; \
			(cd lambda/$$fn/package && zip -r ../function.zip .); \
			(cd lambda/$$fn && zip -g function.zip app.py); \
		else \
			(cd lambda/$$fn && zip -r function.zip app.py); \
		fi; \
	done
	@echo "✅ All Lambdas zipped."

deploy:
	@echo "🚀 Deploying Lambda functions to LocalStack..."
	$(foreach fn,$(LAMBDA_NAMES), \
	aws $(ENDPOINT) $(AWS_OPTS) lambda create-function \
		--function-name $(fn)-function \
		--runtime python3.8 \
		--handler app.lambda_handler \
		--zip-file fileb://lambda/$(fn)/function.zip \
		--role $(ROLE_ARN) || echo "⚠️  Skipped $(fn) (already exists)";)
	@echo "✅ Deployment complete."

update:
	@echo "🔁 Updating Lambda functions..."
	$(foreach fn,$(LAMBDA_NAMES), \
	aws $(ENDPOINT) $(AWS_OPTS) lambda update-function-code \
		--function-name $(fn)-function \
		--zip-file fileb://lambda/$(fn)/function.zip;)
	@echo "✅ Code updated."

update-config:
	@echo "🔧 Updating Lambda configurations..."
	$(foreach fn,$(LAMBDA_NAMES), \
	aws $(ENDPOINT) $(AWS_OPTS) lambda update-function-configuration \
		--function-name $(fn)-function \
		--timeout 30;)
	@echo "✅ Configurations updated."

clean:
	@echo "🧹 Deleting Lambda functions..."
	$(foreach fn,$(LAMBDA_NAMES), \
	aws $(ENDPOINT) $(AWS_OPTS) lambda delete-function \
		--function-name $(fn)-function || true;)
	@echo "✅ Functions deleted."

clean-deps:
	@echo "🧹 Cleaning up dependencies..."
	@rm -rf lambda/pdf_listener/package lambda/pdf_listener/venv
	@echo "✅ Dependencies cleaned."

list:
	@echo "📋 Listing deployed functions..."
	@aws $(ENDPOINT) $(AWS_OPTS) lambda list-functions

# Deploying Assessment AI Application on Azure Cloud

This comprehensive guide will walk you through the process of deploying the Assessment AI application on Microsoft Azure Cloud. The guide covers everything from setting up Azure resources to configuring the application for production use.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure Account Setup](#azure-account-setup)
3. [Database Setup with Azure SQL](#database-setup-with-azure-sql)
4. [Application Deployment with Azure App Service](#application-deployment-with-azure-app-service)
5. [Environment Configuration](#environment-configuration)
6. [Continuous Deployment Setup](#continuous-deployment-setup)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Scaling and Performance Optimization](#scaling-and-performance-optimization)
9. [Security Best Practices](#security-best-practices)
10. [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Prerequisites

Before starting the deployment process, ensure you have the following:

- Assessment AI application source code
- Python 3.11 or later installed on your local machine
- Git installed on your local machine
- Azure CLI installed (for command-line deployment)
- Visual Studio Code with Azure extensions (optional, for GUI-based deployment)

## Azure Account Setup

1. **Create an Azure Account**:
   - Visit [Azure Portal](https://portal.azure.com)
   - Sign up for a new account or log in to an existing one
   - If you're new to Azure, you can sign up for a free trial with $200 credit

2. **Create a Resource Group**:
   ```bash
   az login
   az group create --name AssessmentAIResourceGroup --location eastus
   ```

3. **Set up Azure CLI for deployment**:
   ```bash
   az configure --defaults group=AssessmentAIResourceGroup
   ```

## Database Setup with Azure SQL

1. **Create an Azure SQL Server**:
   ```bash
   az sql server create \
     --name assessment-ai-sql-server \
     --resource-group AssessmentAIResourceGroup \
     --location eastus \
     --admin-user dbadmin \
     --admin-password "YourStrongPassword123!"
   ```

2. **Configure Firewall Rules**:
   ```bash
   # Allow Azure services
   az sql server firewall-rule create \
     --server assessment-ai-sql-server \
     --name AllowAzureServices \
     --start-ip-address 0.0.0.0 \
     --end-ip-address 0.0.0.0
   
   # Allow your IP address for development
   az sql server firewall-rule create \
     --server assessment-ai-sql-server \
     --name AllowMyIP \
     --start-ip-address <your-ip-address> \
     --end-ip-address <your-ip-address>
   ```

3. **Create a Database**:
   ```bash
   az sql db create \
     --server assessment-ai-sql-server \
     --name AssessmentAIDB \
     --service-objective S0 \
     --zone-redundant false
   ```

4. **Get Connection String**:
   ```bash
   az sql db show-connection-string \
     --server assessment-ai-sql-server \
     --name AssessmentAIDB \
     --client sqlalchemy
   ```

   Save the connection string for later use. It will look something like:
   ```
   mssql+pyodbc://<username>:<password>@<server-name>.database.windows.net:1433/<database-name>?driver=ODBC+Driver+17+for+SQL+Server
   ```

## Application Deployment with Azure App Service

1. **Create an App Service Plan**:
   ```bash
   az appservice plan create \
     --name AssessmentAIPlan \
     --resource-group AssessmentAIResourceGroup \
     --sku B1 \
     --is-linux
   ```

2. **Create a Web App**:
   ```bash
   az webapp create \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup \
     --plan AssessmentAIPlan \
     --runtime "PYTHON|3.11" \
     --deployment-local-git
   ```

3. **Configure Application Settings**:
   ```bash
   az webapp config appsettings set \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup \
     --settings \
     FLASK_APP=src/main.py \
     FLASK_ENV=production \
     DB_USERNAME=dbadmin \
     DB_PASSWORD="YourStrongPassword123!" \
     DB_HOST=assessment-ai-sql-server.database.windows.net \
     DB_PORT=1433 \
     DB_NAME=AssessmentAIDB \
     SECRET_KEY="your-secret-key-here"
   ```

4. **Configure Startup Command**:
   ```bash
   az webapp config set \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup \
     --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 --chdir src 'main:create_app()'"
   ```

5. **Prepare Application for Deployment**:
   - Update your `requirements.txt` to include gunicorn:
     ```
     gunicorn==21.2.0
     pyodbc==4.0.39
     ```
   - Create a `.deployment` file in your project root:
     ```
     [config]
     SCM_DO_BUILD_DURING_DEPLOYMENT=true
     ```

6. **Deploy the Application**:
   ```bash
   # Initialize git repository if not already done
   git init
   git add .
   git commit -m "Initial commit for Azure deployment"
   
   # Add Azure as a remote
   git remote add azure <deployment-local-git-url>
   
   # Push to Azure
   git push azure main
   ```

   The deployment URL will be provided when you created the web app with the `--deployment-local-git` flag.

## Environment Configuration

1. **Configure CORS (if needed)**:
   ```bash
   az webapp cors add \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup \
     --allowed-origins "https://yourdomain.com"
   ```

2. **Set up Custom Domain (optional)**:
   ```bash
   # Add hostname
   az webapp config hostname add \
     --webapp-name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup \
     --hostname yourdomain.com
   
   # Add SSL binding (requires certificate)
   az webapp config ssl bind \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup \
     --certificate-thumbprint <certificate-thumbprint> \
     --ssl-type SNI
   ```

3. **Configure Application Insights for Monitoring**:
   ```bash
   # Create Application Insights resource
   az monitor app-insights component create \
     --app assessment-ai-insights \
     --location eastus \
     --resource-group AssessmentAIResourceGroup
   
   # Get the instrumentation key
   instrumentationKey=$(az monitor app-insights component show \
     --app assessment-ai-insights \
     --resource-group AssessmentAIResourceGroup \
     --query instrumentationKey \
     --output tsv)
   
   # Add the instrumentation key to app settings
   az webapp config appsettings set \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup \
     --settings APPINSIGHTS_INSTRUMENTATIONKEY=$instrumentationKey
   ```

## Continuous Deployment Setup

1. **Set up GitHub Actions**:
   - Create a `.github/workflows/azure-deploy.yml` file in your repository:

   ```yaml
   name: Deploy to Azure
   
   on:
     push:
       branches: [ main ]
   
   jobs:
     build-and-deploy:
       runs-on: ubuntu-latest
       
       steps:
       - uses: actions/checkout@v2
       
       - name: Set up Python
         uses: actions/setup-python@v2
         with:
           python-version: '3.11'
           
       - name: Install dependencies
         run: |
           python -m pip install --upgrade pip
           pip install -r requirements.txt
           
       - name: Run tests
         run: |
           python -m unittest discover tests
           
       - name: Deploy to Azure Web App
         uses: azure/webapps-deploy@v2
         with:
           app-name: 'assessment-ai-app'
           publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
           package: .
   ```

2. **Configure GitHub Secrets**:
   - In your GitHub repository, go to Settings > Secrets
   - Add a new secret named `AZURE_WEBAPP_PUBLISH_PROFILE`
   - Get the publish profile from Azure:
     ```bash
     az webapp deployment list-publishing-profiles \
       --name assessment-ai-app \
       --resource-group AssessmentAIResourceGroup \
       --xml
     ```
   - Copy the output and paste it as the value for the secret

## Monitoring and Logging

1. **Enable Diagnostic Logs**:
   ```bash
   az webapp log config \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup \
     --application-logging true \
     --detailed-error-messages true \
     --failed-request-tracing true \
     --web-server-logging filesystem
   ```

2. **Stream Logs**:
   ```bash
   az webapp log tail \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup
   ```

3. **Set up Alerts**:
   ```bash
   # Create an action group for email notifications
   az monitor action-group create \
     --name AssessmentAIAlertGroup \
     --resource-group AssessmentAIResourceGroup \
     --action email admin admin@yourdomain.com
   
   # Create an alert for high CPU usage
   az monitor metrics alert create \
     --name "High CPU Alert" \
     --resource-group AssessmentAIResourceGroup \
     --scopes $(az webapp show --name assessment-ai-app --resource-group AssessmentAIResourceGroup --query id --output tsv) \
     --condition "avg Percentage CPU > 80" \
     --window-size 5m \
     --action $(az monitor action-group show --name AssessmentAIAlertGroup --resource-group AssessmentAIResourceGroup --query id --output tsv)
   ```

## Scaling and Performance Optimization

1. **Configure Autoscaling**:
   ```bash
   az monitor autoscale create \
     --name AssessmentAIAutoscale \
     --resource-group AssessmentAIResourceGroup \
     --resource $(az webapp show --name assessment-ai-app --resource-group AssessmentAIResourceGroup --query id --output tsv) \
     --min-count 1 \
     --max-count 5 \
     --count 1
   
   # Add a scale rule based on CPU percentage
   az monitor autoscale rule create \
     --autoscale-name AssessmentAIAutoscale \
     --resource-group AssessmentAIResourceGroup \
     --scale out 1 \
     --condition "Percentage CPU > 70 avg 5m"
   
   # Add a scale-in rule
   az monitor autoscale rule create \
     --autoscale-name AssessmentAIAutoscale \
     --resource-group AssessmentAIResourceGroup \
     --scale in 1 \
     --condition "Percentage CPU < 30 avg 5m"
   ```

2. **Enable Azure CDN for Static Content**:
   ```bash
   # Create a CDN profile
   az cdn profile create \
     --name AssessmentAICDN \
     --resource-group AssessmentAIResourceGroup \
     --sku Standard_Microsoft
   
   # Create a CDN endpoint
   az cdn endpoint create \
     --name assessment-ai-cdn \
     --profile-name AssessmentAICDN \
     --resource-group AssessmentAIResourceGroup \
     --origin assessment-ai-app.azurewebsites.net \
     --origin-host-header assessment-ai-app.azurewebsites.net \
     --enable-compression
   ```

## Security Best Practices

1. **Enable Azure Security Center**:
   ```bash
   az security center pricing update --name AppServices --tier Standard
   ```

2. **Configure Web Application Firewall (WAF)**:
   ```bash
   # Create Application Gateway with WAF
   az network application-gateway create \
     --name AssessmentAIAppGateway \
     --resource-group AssessmentAIResourceGroup \
     --location eastus \
     --vnet-name AssessmentAIVNet \
     --subnet AppGatewaySubnet \
     --capacity 2 \
     --sku WAF_v2 \
     --http-settings-cookie-based-affinity Disabled \
     --frontend-port 80 \
     --http-settings-port 80 \
     --http-settings-protocol Http \
     --public-ip-address AssessmentAIPublicIP
   
   # Enable WAF
   az network application-gateway waf-config set \
     --gateway-name AssessmentAIAppGateway \
     --resource-group AssessmentAIResourceGroup \
     --enabled true \
     --firewall-mode Prevention \
     --rule-set-version 3.1
   ```

3. **Enable HTTPS Only**:
   ```bash
   az webapp update \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup \
     --https-only true
   ```

4. **Configure Authentication (optional)**:
   ```bash
   az webapp auth update \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup \
     --enabled true \
     --action LoginWithAzureActiveDirectory \
     --aad-allowed-token-audiences "https://assessment-ai-app.azurewebsites.net/.auth/login/aad/callback" \
     --aad-client-id <your-aad-client-id> \
     --aad-client-secret <your-aad-client-secret> \
     --aad-token-issuer-url "https://sts.windows.net/<your-tenant-id>/"
   ```

## Troubleshooting Common Issues

### Database Connection Issues

1. **Check Firewall Rules**:
   ```bash
   az sql server firewall-rule list \
     --server assessment-ai-sql-server \
     --resource-group AssessmentAIResourceGroup
   ```

2. **Verify Connection String**:
   - Ensure the connection string in your application settings is correct
   - Check that the username and password are properly escaped

### Deployment Failures

1. **Check Deployment Logs**:
   ```bash
   az webapp log deployment show \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup
   ```

2. **Verify Python Version**:
   ```bash
   az webapp config show \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup \
     --query linuxFxVersion
   ```

### Application Errors

1. **Check Application Logs**:
   ```bash
   az webapp log tail \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup
   ```

2. **SSH into Web App for Debugging**:
   ```bash
   az webapp ssh \
     --name assessment-ai-app \
     --resource-group AssessmentAIResourceGroup
   ```

### Performance Issues

1. **Check Resource Utilization**:
   ```bash
   az monitor metrics list \
     --resource $(az webapp show --name assessment-ai-app --resource-group AssessmentAIResourceGroup --query id --output tsv) \
     --metric "CpuPercentage" "MemoryPercentage" \
     --interval 5m
   ```

2. **Analyze Application Insights Data**:
   - Visit the Azure Portal
   - Navigate to your Application Insights resource
   - Check Performance, Failures, and User behavior analytics

## Conclusion

You have now successfully deployed the Assessment AI application on Azure Cloud. The application is configured for production use with proper security, monitoring, and scaling capabilities. For further assistance or advanced configurations, refer to the [Azure documentation](https://docs.microsoft.com/en-us/azure/) or contact Azure support.

Remember to regularly update your application and dependencies to ensure security and performance. Monitor your application's performance and costs to optimize your Azure resources as needed.

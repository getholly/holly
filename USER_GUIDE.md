# Holly User Guide

Welcome to Holly! This comprehensive guide will walk you through getting started with the platform, from creating your account to having productive AI-assisted coding conversations.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Account Setup and Authentication](#account-setup-and-authentication)
3. [Connecting Your GitHub Account](#connecting-your-github-account)
4. [Creating a Mission](#creating-a-mission)
5. [Using the Chat Interface](#using-the-chat-interface)
6. [Managing LLMs and API Keys](#managing-llms-and-api-keys)
7. [Dashboard Overview](#dashboard-overview)
8. [Settings and Customization](#settings-and-customization)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

Get up and running with Holly in just a few steps:

1. **Create an account** - Register with your email and password
2. **Connect GitHub** - Link your GitHub account to access your repositories
3. **Create a Mission** - Use the wizard to set up a project with repositories, tools, and knowledge
4. **Start coding** - Begin a conversation with Holly to work on your code

---

## Account Setup and Authentication

### Creating a New Account

1. **Navigate to the registration page**
   - Go to `/register` or click "Create an Account" from the login page

2. **Enter your details**
   - **Email**: Enter a valid email address (this will be your username)
   - **Password**: Create a secure password

3. **Accept Terms and Privacy Policy**
   - Read and check the box to agree to the Terms and Conditions and Privacy Policy
   - These links open in new tabs so you can review them without losing your progress

4. **Create your account**
   - Click the "Create account" button
   - You'll receive a confirmation message about email verification
   - Check your email for a verification link

5. **Verify your email**
   - Click the verification link in your email
   - This activates your account

### Logging In

1. **Navigate to the login page**
   - Go to `/login`

2. **Enter your credentials**
   - **Email**: Your registered email address
   - **Password**: Your account password

3. **Optional: Remember Me**
   - Check "Remember me" to save your email for future logins

4. **Sign in**
   - Click "Log in to your account"
   - You'll be redirected to the dashboard upon successful login

### Password Recovery

If you've forgotten your password:

1. Click "Forgotten Password?" on the login page
2. Enter your email address
3. Check your email for a password reset link
4. Follow the link to create a new password

---

## Connecting Your GitHub Account

Before you can work with your repositories, you need to connect your GitHub account to Holly.

### How to Connect

1. **Navigate to GitHub Connect**
   - Go to `/github/connect` from the navigation menu
   - Or click "GitHub" from the dashboard quick actions

2. **Check connection status**
   - If already connected, you'll see your GitHub username and avatar
   - The page shows how many accounts are connected

3. **Connect a new account**
   - If not connected, click "Connect to GitHub"
   - You'll be redirected to GitHub for authorization

4. **Authorize Holly**
   - Review the permissions Holly is requesting
   - Click "Authorize" to grant access
   - You'll be redirected back to Holly

5. **Confirmation**
   - Once connected, you'll see "Your GitHub account is already connected!"
   - Your GitHub username and avatar will be displayed

### What Happens After Connection

After connecting your GitHub account:

- Holly can access your repositories (public and private, depending on permissions)
- You can select repositories in the Mission wizard
- Repository branches become available for selection
- You can manage multiple GitHub accounts from the accounts page

### Managing GitHub Accounts

- **View accounts**: Go to `/github/accounts` to see all connected accounts
- **Add another account**: You can connect multiple GitHub accounts
- **Primary account**: The first connected account becomes your primary account

---

## Creating a Mission

A Mission is the core organizational unit in Holly. It combines:
- **Repositories** - Your GitHub code repositories
- **Tools** - AI capabilities and integrations
- **Knowledge Base** - Reference documents and context
- **LLM Model** - The AI model to use for conversations

### Using the Project Setup Wizard

The wizard guides you through creating a Mission in 6 easy steps.

#### Step 1: Branch Name

1. **Navigate to the Wizard**
   - Go to `/wizard` from the dashboard or navigation menu

2. **Enter a branch name**
   - This is a label/identifier for your mission
   - Examples: "feature-auth", "bugfix-login", "refactor-api"
   - Maximum 50 characters
   - This will be used as part of your Mission title

3. **Continue**
   - Press Enter or click "Next" to proceed

#### Step 2: Select Repositories

1. **View available repositories**
   - Your connected GitHub repositories are listed
   - Shows both public and private repositories
   - Displays the count of repositories found

2. **Search and filter**
   - Use the search box to filter repositories by name
   - Toggle "Private Only" to show only private repositories

3. **Select repositories**
   - Check the box next to each repository you want to include
   - You can select multiple repositories for a single Mission

4. **Choose branches**
   - After selecting a repository, its branches load automatically
   - Select the specific branch you want to work with
   - Default branch is typically "main"

5. **Review selection**
   - Selected repositories appear below with their chosen branches
   - You can change branch selections before proceeding

6. **Refresh if needed**
   - Click "Refresh" to reload the repository list if you've recently added repos to GitHub

#### Step 3: Choose LLM Model

1. **View available models**
   - A dropdown shows all configured LLM models
   - These include system models and any custom models you've added

2. **Select a model**
   - Click the dropdown and choose your preferred AI model
   - The first available model is selected by default

3. **Model considerations**
   - Different models have different capabilities and costs
   - Some models may be better suited for specific tasks
   - You can change this later by creating a new conversation

#### Step 4: Select Tools

1. **View available tools**
   - Tools are listed with checkboxes
   - Each tool has a name and description

2. **Select tools**
   - Check the box next to tools you want to enable for this Mission
   - Tools extend Holly's capabilities (e.g., file editing, code execution)
   - You can select multiple tools or none

3. **Scroll through options**
   - If many tools are available, scroll to see them all
   - The panel is scrollable for better navigation

#### Step 5: Select Knowledge

1. **View knowledge items**
   - Knowledge base items provide additional context to the AI
   - Each item has a name and summary

2. **Select knowledge**
   - Check items relevant to your project
   - Knowledge helps Holly understand your project better
   - Examples: coding standards, architecture docs, API references

3. **Optional selection**
   - Knowledge selection is optional
   - Select only items relevant to your work

#### Step 6: Project Description

1. **Describe your goals**
   - Enter a detailed description of what you want to accomplish
   - Be specific about your objectives
   - This helps Holly understand your intent

2. **Example descriptions**
   - "Implement user authentication with OAuth2 and JWT tokens"
   - "Fix the memory leak in the data processing pipeline"
   - "Refactor the API endpoints to follow REST best practices"

3. **Finish setup**
   - Press Ctrl+Enter (or Cmd+Enter on Mac) to complete
   - Or click the "Finish" button

### After Creating a Mission

1. **Mission creation**
   - Holly creates your Mission with all selected options
   - A loading overlay shows progress

2. **Automatic conversation creation**
   - An initial conversation is created for your Mission
   - You're automatically redirected to the chat interface

3. **Start working**
   - You can now begin chatting with Holly about your code
   - Your selected repositories and tools are active

### Mission States

Missions have different states:

- **Active** - Ready for conversations
- **Container Running** - A development container is active (shown as green indicator)
- **Not started** - Container not yet initialized (shown as red indicator)

---

## Using the Chat Interface

The chat interface is where you interact with Holly to work on your code.

### Chat Interface Layout

The chat screen has several components:

1. **Mission Bar** (top)
   - Dropdown to select active Mission
   - Shows Mission details: title, branch, repository count, state
   - "Edit Mission" and "Delete Mission" buttons

2. **Side Panel** (left)
   - Conversation History - list of previous chats
   - Conversations grouped by date
   - Click any conversation to load it
   - Delete conversations with the trash icon

3. **Chat Area** (main)
   - Message display area
   - Shows your messages and Holly's responses
   - Scrollable history

4. **Input Area** (bottom)
   - Text input for your messages
   - Send button to submit
   - LLM model selector

### Starting a New Conversation

1. **Select a Mission**
   - Use the dropdown in the Mission bar
   - Or create a new Mission first via the wizard

2. **Type your message**
   - Enter your question, task, or instruction in the input area
   - Be specific and clear about what you need

3. **Send the message**
   - Click the send button or press Enter
   - Your message appears in the chat
   - Holly processes and responds

### Conversation Features

- **Persistent history** - Conversations are saved automatically
- **Multiple conversations** - Create many conversations per Mission
- **Date grouping** - History is organized by date for easy navigation
- **Delete conversations** - Remove old or irrelevant chats

### Working with Conversations

**To continue a previous conversation:**
1. Click on it in the Conversation History panel
2. The chat loads with all previous messages
3. Continue where you left off

**To start a fresh conversation:**
1. Ensure you have a Mission selected
2. Type a new message
3. A new conversation is created automatically

### Tips for Effective Conversations

1. **Be specific** - Clear instructions get better results
2. **Provide context** - Reference specific files or functions
3. **Break down tasks** - Split complex tasks into smaller steps
4. **Review responses** - Holly's code suggestions should be reviewed
5. **Iterate** - Refine your requests based on responses

### Settings Access

- Click the "Settings" button at the bottom of the side panel
- Opens a settings modal for customization options

---

## Managing LLMs and API Keys

Holly supports multiple LLM (Large Language Model) providers. You can configure models and API keys from the LLM Management page.

### Accessing LLM Management

1. Navigate to `/llms` from the navigation menu
2. View all configured models in a table

### Model Types

- **System** (blue badge) - Pre-configured models, read-only
- **Custom** (green badge) - User-added models, fully editable

### Adding a Custom LLM

1. **Click "Add Custom LLM"**
   - Opens a modal form

2. **Fill in the details**
   - **Name** (required): Display name (e.g., "My GPT-4")
   - **Model ID** (required): Provider/model format (e.g., "openai/gpt-4")
   - **Base URL** (optional): Custom API endpoint, leave empty for default
   - **System Prompt** (optional): Default system message
   - **Temperature**: Creativity level (0-2, default 0.7)
   - **Max Tokens**: Response length limit

3. **Create the model**
   - Click "Create LLM"
   - The model appears in the table

### Managing API Keys

API keys authenticate your requests to LLM providers.

**To add an API key:**
1. Find the model in the table
2. Click "Add Key" in the API Key column
3. Enter your API key
4. Click the green checkmark to save

**To update an API key:**
1. Click the edit icon next to the existing key
2. Enter the new key
3. Save changes

**To remove an API key:**
1. Click the trash icon next to the key
2. Confirm deletion

### Editing Custom Models

1. Click the edit icon in the Actions column
2. Modify fields directly in the table
3. Click the green checkmark to save
4. Click the red X to cancel

### Deleting Custom Models

1. Click the trash icon for the model
2. Confirm deletion in the modal
3. Note: This cannot be undone

### Searching Models

- Use the search box to filter models by name, ID, URL, or prompt
- Helpful when you have many configured models

---

## Dashboard Overview

The dashboard (`/dashboard`) is your home screen after logging in.

### Dashboard Components

1. **Mission Bar**
   - Quick access to your Missions
   - Same controls as the chat interface

2. **Welcome Header**
   - Personalized greeting with your email
   - Quick actions and recent activity summary

3. **Quick Actions**
   - **Chat** - Go directly to the chat interface
   - **GitHub** - Manage repository connections
   - **Wizard** - Create a new Mission

4. **Stats**
   - Number of Missions
   - Connected Repositories
   - Total Conversations

5. **Recent Conversations**
   - Last 5 conversations with dates
   - Click to continue any conversation

### Navigation Tips

- Use quick action cards to navigate efficiently
- Dashboard provides an overview of your Holly activity
- Stats update automatically as you use the platform

---

## Settings and Customization

### Accessing Settings

- Click "Settings" button in the chat side panel
- Opens the Settings Modal

### Available Settings

Settings may include:

- Theme preferences (light/dark mode)
- Notification settings
- Default LLM selection
- Interface customizations

### Mission Settings

From the Mission bar:

1. **Edit Mission** - Opens a tabbed modal with:
   - **Details tab** - Edit title, description, branch name
   - **Repositories tab** - Add or remove repositories

2. **Delete Mission** - Permanently removes a Mission
   - Confirmation required
   - Cannot be undone

### Editing Mission Repositories

1. Click "Edit Mission" in the Mission bar
2. Go to the "Repositories" tab
3. **Current Repositories** - Shows connected repos with remove option
4. **Add Repositories** - Use the repo selector to add more
5. Click "Add Repositories to Mission" to save

---

## Troubleshooting

### Common Issues and Solutions

#### "Authentication error" when creating a Mission

**Cause**: Your session may have expired

**Solution**:
1. Refresh the page
2. Log out and log back in
3. Clear browser cookies and try again

#### Can't see repositories in the wizard

**Cause**: GitHub connection issue

**Solution**:
1. Go to `/github/connect` and verify connection
2. Reconnect your GitHub account if needed
3. Check GitHub permissions for Holly
4. Click "Refresh" in the repository selector

#### LLM errors when chatting

**Cause**: Missing or invalid API key

**Solution**:
1. Go to `/llms`
2. Find the model you're using
3. Add or update the API key
4. Ensure the key is valid with the provider

#### Messages not sending

**Cause**: No Mission selected

**Solution**:
1. Select a Mission from the dropdown
2. Or create a new Mission via the wizard
3. Then try sending your message again

#### Conversation history not loading

**Cause**: Mission not properly selected

**Solution**:
1. Refresh the page
2. Reselect your Mission
3. Check that the Mission has conversations

#### GitHub OAuth redirect fails

**Cause**: Network or configuration issue

**Solution**:
1. Check your internet connection
2. Try again after a few minutes
3. Clear browser cache
4. Contact support if the issue persists

### Getting Help

If you encounter issues not covered here:

1. Check the browser console for error messages (F12 > Console)
2. Try refreshing the page
3. Log out and back in
4. Clear browser cache and cookies
5. Report issues to the development team

### Browser Requirements

For best experience, use:
- Modern browsers (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- Cookies enabled
- Stable internet connection

---

## Keyboard Shortcuts

### Wizard Navigation
- **Enter** - Proceed to next step (except in text areas)
- **Ctrl+Enter** / **Cmd+Enter** - Finish wizard from project description

### Chat Interface
- **Enter** - Send message
- **Escape** - Close modals

---

## Glossary

- **Mission** - A project configuration combining repositories, tools, knowledge, and LLM settings
- **LLM** - Large Language Model, the AI that powers conversations
- **Knowledge Base** - Reference documents that provide context to the AI
- **Tools** - Capabilities that extend what Holly can do
- **Conversation** - A chat session within a Mission
- **Branch** - A Git branch in your repository

---

## Best Practices

1. **Organize with Missions** - Create separate Missions for different projects or features
2. **Choose the right LLM** - Select models based on task complexity
3. **Provide context** - Use descriptions and knowledge items effectively
4. **Review code changes** - Always review Holly's suggestions before applying
5. **Keep conversations focused** - Start new conversations for different tasks
6. **Manage API keys securely** - Don't share keys, rotate them periodically

---

Thank you for using Holly! We hope this guide helps you get the most out of the platform.

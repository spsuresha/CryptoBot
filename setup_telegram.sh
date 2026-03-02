#!/bin/bash
# Telegram Setup Helper

echo "=========================================="
echo "TELEGRAM BOT SETUP"
echo "=========================================="
echo ""
echo "Follow these steps:"
echo ""
echo "1. Open Telegram and search for @BotFather"
echo "2. Send: /newbot"
echo "3. Follow instructions to create your bot"
echo "4. Copy the BOT TOKEN"
echo ""
echo "5. Search for @userinfobot"
echo "6. Start chat to get your CHAT ID"
echo ""
echo "=========================================="
echo ""

read -p "Enter your Telegram Bot Token: " 8614592734:AAGi39FbmlpEauvD5t-54t8EQoeuYxQlnn0
read -p "Enter your Telegram Chat ID: " 6511865187

# Backup original .env
cp .env .env.backup

# Update .env file
sed -i "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$BOT_TOKEN|" .env
sed -i "s|TELEGRAM_CHAT_ID=.*|TELEGRAM_CHAT_ID=$CHAT_ID|" .env

echo ""
echo "✓ .env file updated!"
echo "✓ Backup saved to .env.backup"
echo ""
echo "Now restart your bot:"
echo "  ./stop_paper_trading.sh"
echo "  ./start_paper_trading.sh"
echo ""

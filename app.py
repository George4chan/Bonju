from flask import Flask, render_template_string, request, jsonify, session, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import base64
import uuid
import hashlib
from datetime import datetime, timedelta
import mimetypes
import threading
import time
import random
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nexachat-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Data storage (in-memory for demo, use database in production)
users = {}
chats = {}
groups = {}
status_updates = {}
blocked_users = {}
user_sessions = {}
online_users = set()

# HTML Template (original HTML with modifications for Flask)
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexaChat - Next Generation Messaging</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/emoji-picker-element@1.12.0/dist/index.min.css">
    <style>
        /* CSS Reset & Base Styles */
        :root {
            --primary: #6c5ce7;
            --primary-dark: #5649c0;
            --primary-light: #8579ec;
            --primary-ultralight: #f0eefc;
            --secondary: #00b894;
            --dark: #2d3436;
            --darker: #1e272e;
            --light: #ffffff;
            --gray: #636e72;
            --gray-dark: #4a5357;
            --gray-light: #dfe6e9;
            --gray-ultralight: #f5f6fa;
            --chat-incoming: #ffffff;
            --chat-outgoing: #e3f2fd;
            --chat-outgoing-dark: #3a4e5a;
            --danger: #d63031;
            --success: #00b894;
            --warning: #fdcb6e;
            --info: #0984e3;
            --border-radius: 10px;
            --border-radius-lg: 15px;
            --border-radius-xl: 20px;
            --shadow-sm: 0 2px 4px 0 rgba(0, 0, 0, 0.05);
            --shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
            --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 20px rgba(0, 0, 0, 0.1);
            --shadow-xl: 0 15px 30px rgba(0, 0, 0, 0.15);
            --transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-slow: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            --gradient-primary: linear-gradient(135deg, var(--primary), var(--primary-dark));
            --status-gradient: linear-gradient(135deg, #6c5ce7 0%, #0984e3 100%);
            --status-dot-active: #00b894;
            --status-dot-inactive: rgba(255, 255, 255, 0.3);
            --glass-effect: rgba(255, 255, 255, 0.15);
            --glass-border: rgba(255, 255, 255, 0.2);
            --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
            --neon-primary: 0 0 15px rgba(108, 92, 231, 0.5);
            --neon-success: 0 0 15px rgba(0, 184, 148, 0.5);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        }

        body {
            background-color: var(--light);
            color: var(--dark);
            line-height: 1.6;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        body.dark-mode {
            --light: #1e272e;
            --dark: #dfe6e9;
            --gray-light: #2d3436;
            --gray-ultralight: #252e35;
            --gray-dark: #b2bec3;
            --chat-incoming: #2d3436;
            --chat-outgoing: #3a4e5a;
            --chat-outgoing-dark: #2c3e50;
            --gray: #b2bec3;
            --primary-ultralight: #2c3e50;
            background-color: #121a21;
            color: var(--dark);
        }

        /* Glassmorphism effect */
        .glass {
            background: var(--glass-effect);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            box-shadow: var(--glass-shadow);
        }

        /* Neon effect */
        .neon-primary {
            box-shadow: var(--neon-primary);
        }

        .neon-success {
            box-shadow: var(--neon-success);
        }

        /* Auth Container */
        .auth-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: var(--gradient-primary);
            padding: 20px;
            background-image: radial-gradient(circle at 10% 20%, rgba(108, 92, 231, 0.1) 0%, rgba(86, 73, 192, 0.2) 90%);
        }

        .auth-card {
            background-color: white;
            border-radius: var(--border-radius-xl);
            box-shadow: var(--shadow-xl);
            width: 100%;
            max-width: 450px;
            overflow: hidden;
            transform: translateY(0);
            transition: var(--transition);
            animation: fadeInUp 0.6s ease-out;
            position: relative;
            overflow: hidden;
        }

        .auth-card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
            transform: rotate(30deg);
            pointer-events: none;
        }

        .auth-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }

        .auth-header {
            padding: 40px 30px;
            text-align: center;
            background: var(--gradient-primary);
            color: white;
            position: relative;
            overflow: hidden;
        }

        .auth-header::after {
            content: '';
            position: absolute;
            bottom: -50px;
            right: -50px;
            width: 150px;
            height: 150px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
        }

        .auth-header::before {
            content: '';
            position: absolute;
            top: -50px;
            left: -50px;
            width: 150px;
            height: 150px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
        }

        .auth-logo {
            font-size: 2.5rem;
            margin-bottom: 15px;
            display: inline-flex;
            justify-content: center;
            align-items: center;
            width: 80px;
            height: 80px;
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            backdrop-filter: blur(5px);
            z-index: 1;
            position: relative;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }

        .auth-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 5px;
            position: relative;
            z-index: 1;
        }

        .auth-subtitle {
            font-size: 0.9375rem;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }

        .auth-form {
            padding: 30px;
            position: relative;
            display: none;
        }

        .auth-form.active {
            display: block;
        }

        .form-group {
            margin-bottom: 25px;
            position: relative;
        }

        .form-label {
            display: block;
            margin-bottom: 10px;
            font-size: 0.9375rem;
            font-weight: 500;
            color: var(--dark);
        }

        .form-control {
            width: 100%;
            padding: 14px 18px;
            border: 1px solid var(--gray-light);
            border-radius: var(--border-radius);
            font-size: 1rem;
            transition: var(--transition);
            background-color: white;
            box-shadow: var(--shadow-sm);
        }

        .form-control:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.2);
        }

        body.dark-mode .form-control:focus {
            background-color: #2d3436;
        }

        .input-group {
            display: flex;
        }

        .input-group-prepend {
            display: flex;
            align-items: center;
            padding: 0 14px;
            background-color: var(--gray-light);
            border: 1px solid var(--gray-light);
            border-radius: var(--border-radius) 0 0 var(--border-radius);
            font-size: 0.9375rem;
        }

        .input-group input {
            border-radius: 0 var(--border-radius) var(--border-radius) 0;
            flex: 1;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 14px 28px;
            border-radius: var(--border-radius);
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            border: none;
            text-decoration: none;
            box-shadow: var(--shadow-sm);
        }

        .btn-primary {
            background-color: var(--primary);
            color: white;
            width: 100%;
        }

        .btn-primary:hover {
            background-color: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .btn-outline {
            background-color: transparent;
            border: 1px solid var(--gray-light);
            color: var(--dark);
        }

        .btn-outline:hover {
            background-color: var(--gray-light);
            box-shadow: var(--shadow-sm);
        }

        .auth-footer {
            text-align: center;
            margin-top: 25px;
            font-size: 0.9375rem;
            color: var(--gray-dark);
        }

        .auth-footer a {
            color: var(--primary);
            font-weight: 500;
            text-decoration: none;
        }

        .auth-footer a:hover {
            text-decoration: underline;
        }

        /* Avatar Upload */
        .avatar-upload {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: var(--gray-light);
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            position: relative;
            flex-shrink: 0;
        }

        .avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .avatar-sm {
            width: 32px;
            height: 32px;
        }

        .avatar-md {
            width: 48px;
            height: 48px;
        }

        .avatar-lg {
            width: 80px;
            height: 80px;
        }

        .avatar-xl {
            width: 120px;
            height: 120px;
        }

        .avatar-xxl {
            width: 150px;
            height: 150px;
        }

        /* App Container */
        .app-container {
            display: none;
            height: 100vh;
            background-color: var(--light);
        }

        /* Sidebar */
        .sidebar {
            width: 350px;
            background-color: white;
            border-right: 1px solid var(--gray-light);
            display: flex;
            flex-direction: column;
            height: 100%;
            box-shadow: var(--shadow-sm);
            z-index: 10;
            transition: var(--transition);
        }

        body.dark-mode .sidebar {
            background-color: #121a21;
            border-right: 1px solid #2d3436;
        }

        .sidebar-header {
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: var(--light);
            color: var(--dark);
            border-bottom: 1px solid var(--gray-light);
        }

        body.dark-mode .sidebar-header {
            background-color: #1e272e;
            color: var(--dark);
            border-bottom: 1px solid #2d3436;
        }

        .user-profile {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .user-info {
            display: flex;
            flex-direction: column;
        }

        .user-name {
            font-weight: 600;
            font-size: 0.9375rem;
        }

        .user-status {
            font-size: 0.75rem;
            opacity: 0.8;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
            color: var(--gray);
        }

        .user-status:hover {
            text-decoration: underline;
        }

        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--success);
        }

        .sidebar-actions {
            display: flex;
            gap: 15px;
        }

        .sidebar-actions button {
            background: none;
            border: none;
            color: var(--gray-dark);
            font-size: 1.1rem;
            cursor: pointer;
            transition: var(--transition);
            opacity: 0.8;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }

        .sidebar-actions button:hover {
            opacity: 1;
            background-color: var(--gray-light);
            transform: scale(1.1);
        }

        body.dark-mode .sidebar-actions button:hover {
            background-color: #2d3436;
        }

        /* Search */
        .search-bar {
            padding: 15px;
            background-color: var(--light);
            border-bottom: 1px solid var(--gray-light);
        }

        body.dark-mode .search-bar {
            background-color: #121a21;
            border-bottom: 1px solid #2d3436;
        }

        .search-container {
            position: relative;
        }

        .search-container input {
            width: 100%;
            padding: 12px 15px 12px 42px;
            border-radius: var(--border-radius-lg);
            border: none;
            background-color: var(--gray-light);
            font-size: 0.875rem;
            transition: var(--transition);
            color: var(--dark);
        }

        body.dark-mode .search-container input {
            background-color: #2d3436;
            color: var(--dark);
        }

        .search-container input:focus {
            outline: none;
            background-color: white;
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(108, 92, 231, 0.2);
        }

        body.dark-mode .search-container input:focus {
            background-color: #2d3436;
        }

        .search-icon {
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--gray-dark);
            font-size: 0.9375rem;
        }

        /* Chats List */
        .chats-list {
            flex: 1;
            overflow-y: auto;
            background-color: var(--light);
        }

        body.dark-mode .chats-list {
            background-color: #121a21;
        }

        .chat-item {
            display: flex;
            padding: 12px 15px;
            gap: 12px;
            cursor: pointer;
            transition: var(--transition);
            border-bottom: 1px solid var(--gray-light);
            position: relative;
        }

        body.dark-mode .chat-item {
            border-bottom: 1px solid #2d3436;
        }

        .chat-item:hover {
            background-color: var(--primary-ultralight);
        }

        body.dark-mode .chat-item:hover {
            background-color: #1e272e;
        }

        .chat-item.active {
            background-color: var(--primary-ultralight);
        }

        body.dark-mode .chat-item.active {
            background-color: #2d3436;
        }

        .chat-item.unread::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background-color: var(--primary);
        }

        .chat-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            overflow: hidden;
        }

        .chat-info-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }

        .chat-name {
            font-weight: 600;
            font-size: 0.9375rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--dark);
        }

        .chat-time {
            font-size: 0.6875rem;
            color: var(--gray-dark);
            white-space: nowrap;
        }

        .chat-preview {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.8125rem;
            color: var(--gray-dark);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .chat-preview i {
            font-size: 0.75rem;
            color: var(--gray-dark);
        }

        .unread-count {
            background-color: var(--primary);
            color: white;
            font-size: 0.6875rem;
            padding: 2px 6px;
            border-radius: 50%;
            min-width: 20px;
            text-align: center;
        }

        /* Users List */
        .users-list {
            flex: 1;
            overflow-y: auto;
            display: none;
            background-color: var(--light);
        }

        body.dark-mode .users-list {
            background-color: #121a21;
        }

        .user-item {
            padding: 12px 15px;
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            transition: var(--transition);
            border-bottom: 1px solid var(--gray-light);
            position: relative;
        }

        body.dark-mode .user-item {
            border-bottom: 1px solid #2d3436;
        }

        .user-item:hover {
            background-color: var(--primary-ultralight);
        }

        body.dark-mode .user-item:hover {
            background-color: #1e272e;
        }

        .user-info {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            overflow: hidden;
        }

        .user-info-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }

        .user-name {
            font-weight: 600;
            font-size: 0.9375rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--dark);
        }

        .user-status {
            font-size: 0.75rem;
            color: var(--gray-dark);
        }

        .online {
            color: var(--success);
        }

        /* Chat Area */
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
            position: relative;
            background-color: #f5f7fa;
            background-image: url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%236c5ce7' fill-opacity='0.05'%3E%3Cpath d='M50 50c0-5.523 4.477-10 10-10s10 4.477 10 10-4.477 10-10 10c0 5.523-4.477 10-10 10s-10-4.477-10-10 4.477-10 10-10zM10 10c0-5.523 4.477-10 10-10s10 4.477 10 10-4.477 10-10 10c0 5.523-4.477 10-10 10S0 25.523 0 20s4.477-10 10-10zm10 8c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8zm40 40c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8z' /%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        }

        body.dark-mode .chat-area {
            background-color: #0b141a;
            background-image: none;
        }

        /* Empty Chat */
        .empty-chat {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            text-align: center;
            padding: 20px;
            background-color: rgba(245, 247, 251, 0.8);
        }

        body.dark-mode .empty-chat {
            background-color: rgba(18, 26, 33, 0.8);
        }

        .empty-content {
            max-width: 400px;
        }

        .empty-content img {
            width: 200px;
            margin-bottom: 20px;
            filter: grayscale(30%);
            opacity: 0.8;
        }

        body.dark-mode .empty-content img {
            filter: grayscale(30%) brightness(0.8);
        }

        .empty-content h2 {
            font-size: 1.5rem;
            margin-bottom: 10px;
            color: var(--dark);
        }

        .empty-content p {
            font-size: 0.9375rem;
            color: var(--gray-dark);
            margin-bottom: 8px;
        }

        /* Chat Header */
        .chat-header {
            padding: 15px 20px;
            display: none;
            justify-content: space-between;
            align-items: center;
            background-color: var(--light);
            border-bottom: 1px solid var(--gray-light);
            box-shadow: var(--shadow-sm);
            z-index: 5;
        }

        body.dark-mode .chat-header {
            background-color: #1e272e;
            border-bottom: 1px solid #2d3436;
        }

        .chat-user {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .chat-actions {
            display: flex;
            gap: 15px;
        }

        .chat-actions button {
            background: none;
            border: none;
            color: var(--gray-dark);
            font-size: 1.1rem;
            cursor: pointer;
            transition: var(--transition);
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }

        .chat-actions button:hover {
            color: var(--primary);
            background-color: var(--gray-light);
            transform: scale(1.1);
        }

        body.dark-mode .chat-actions button:hover {
            background-color: #2d3436;
        }

        .back-to-chats {
            display: none;
            background: none;
            border: none;
            color: var(--gray-dark);
            font-size: 1.2rem;
            cursor: pointer;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }

        .back-to-chats:hover {
            background-color: var(--gray-light);
        }

        body.dark-mode .back-to-chats:hover {
            background-color: #2d3436;
        }

        /* Messages Container */
        .messages-container {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: none;
            background-color: transparent;
            display: flex;
            flex-direction: column;
        }

        .message {
            max-width: 30%;
            margin-bottom: 16px;
            padding: 12px 16px;
            border-radius: var(--border-radius-lg);
            position: relative;
            word-wrap: break-word;
            animation: fadeIn 0.3s ease-out;
            box-shadow: var(--shadow-sm);
            line-height: 1.4;
            font-size: 0.9375rem;
            word-break: break-word;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .outgoing {
            background-color: var(--chat-outgoing);
            color: #121a21;
            margin-left: auto;
            border-top-right-radius: 0;
            align-self: flex-end;
        }

        body.dark-mode .outgoing {
            background-color: var(--chat-outgoing-dark);
            color: #dfe6e9;
        }

        .incoming {
            background-color: var(--chat-incoming);
            margin-right: auto;
            border-top-left-radius: 0;
            color: var(--dark);
            align-self: flex-start;
        }

        .message-time {
            font-size: 0.6875rem;
            margin-top: 6px;
            text-align: right;
            opacity: 0.8;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 4px;
        }

        .outgoing .message-time {
            color: rgba(0, 0, 0, 0.6);
        }

        body.dark-mode .outgoing .message-time {
            color: rgba(223, 230, 233, 0.6);
        }

        .incoming .message-time {
            color: var(--gray-dark);
        }

        .message-status {
            font-size: 0.75rem;
        }

        .message img {
            max-width: 250px;
            max-height: 250px;
            border-radius: var(--border-radius);
            margin-top: 8px;
            cursor: pointer;
            transition: var(--transition);
            object-fit: cover;
            display: block;
        }

        .message img:hover {
            opacity: 0.9;
        }

        .message-doc {
            display: flex;
            align-items: center;
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: var(--border-radius);
            margin-top: 8px;
        }

        .outgoing .message-doc {
            background-color: rgba(255, 255, 255, 0.1);
        }

        .incoming .message-doc {
            background-color: var(--gray-light);
        }

        body.dark-mode .incoming .message-doc {
            background-color: #2d3436;
        }

        .message-doc i {
            font-size: 1.5rem;
            margin-right: 10px;
            color: var(--primary);
        }

        .outgoing .message-doc i {
            color: white;
        }

        body.dark-mode .outgoing .message-doc i {
            color: #dfe6e9;
        }

        .doc-info {
            flex: 1;
        }

        .doc-name {
            font-weight: 500;
            font-size: 0.875rem;
            margin-bottom: 3px;
        }

        .outgoing .doc-name {
            color: white;
        }

        body.dark-mode .outgoing .doc-name {
            color: #dfe6e9;
        }

        .doc-size {
            font-size: 0.75rem;
            color: var(--gray-dark);
        }

        .outgoing .doc-size {
            color: rgba(255, 255, 255, 0.7);
        }

        body.dark-mode .outgoing .doc-size {
            color: rgba(223, 230, 233, 0.6);
        }

        /* Message Input */
        .message-input {
            padding: 12px 16px;
            display: none;
            align-items: center;
            gap: 10px;
            background-color: var(--light);
            border-top: 1px solid var(--gray-light);
            box-shadow: var(--shadow-sm);
            z-index: 5;
        }

        body.dark-mode .message-input {
            background-color: #1e272e;
            border-top: 1px solid #2d3436;
        }

        .input-actions {
            display: flex;
            gap: 10px;
        }

        .input-actions button {
            background: none;
            border: none;
            color: var(--gray-dark);
            font-size: 1.25rem;
            cursor: pointer;
            transition: var(--transition);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .input-actions button:hover {
            background-color: var(--gray-light);
            color: var(--primary);
        }

        body.dark-mode .input-actions button:hover {
            background-color: #2d3436;
        }

        #message-input {
            flex: 1;
            padding: 12px 16px;
            border-radius: var(--border-radius-lg);
            border: none;
            background-color: var(--gray-light);
            font-size: 0.9375rem;
            resize: none;
            max-height: 120px;
            transition: var(--transition);
            color: var(--dark);
        }

        body.dark-mode #message-input {
            background-color: #2d3436;
            color: var(--dark);
        }

        #message-input:focus {
            outline: none;
            background-color: white;
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(108, 92, 231, 0.2);
        }

        body.dark-mode #message-input:focus {
            background-color: #2d3436;
        }

        #send-btn {
            background-color: var(--primary);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition);
        }

        #send-btn:hover {
            background-color: var(--primary-dark);
            transform: scale(1.05);
        }

        #voice-message-btn {
            display: none;
            background-color: var(--primary);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            align-items: center;
            justify-content: center;
        }

        /* Emoji Picker */
        .emoji-picker-container {
            position: absolute;
            bottom: 70px;
            right: 20px;
            z-index: 100;
            display: none;
            border-radius: var(--border-radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-xl);
        }

        .emoji-picker-container.visible {
            display: block;
        }

        /* File Input */
        #file-input,
        #status-media-input {
            display: none;
        }

        /* Modals */
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            display: none;
            justify-content: center;
            align-items: center;
            backdrop-filter: blur(5px);
        }

        .modal-content {
            background-color: white;
            border-radius: var(--border-radius-xl);
            width: 90%;
            max-width: 500px;
            max-height: 90vh;
            overflow: hidden;
            box-shadow: var(--shadow-xl);
            animation: modalFadeIn 0.3s ease-out;
            transform: translateY(0);
            transition: var(--transition-slow);
        }

        .modal-content:hover {
            transform: translateY(-5px);
        }

        body.dark-mode .modal-content {
            background-color: #2d3436;
        }

        @keyframes modalFadeIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .modal-header {
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--gray-light);
        }

        body.dark-mode .modal-header {
            border-bottom: 1px solid #374248;
        }

        .modal-header h3 {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--dark);
        }

        .close-modal {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--gray-dark);
            transition: var(--transition);
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }

        .close-modal:hover {
            color: var(--danger);
            background-color: var(--gray-light);
            transform: rotate(90deg);
        }

        body.dark-mode .close-modal:hover {
            background-color: #2d3436;
        }

        .modal-body {
            padding: 20px;
            overflow-y: auto;
            max-height: calc(90vh - 120px);
        }

        /* Profile Modal */
        .profile-modal {
            max-width: 500px;
        }

        .profile-header {
            padding: 30px 20px;
            text-align: center;
            background: var(--gradient-primary);
            color: white;
            position: relative;
        }

        .profile-avatar {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            margin: 0 auto 15px;
            overflow: hidden;
            border: 4px solid white;
            position: relative;
            box-shadow: var(--shadow-lg);
        }

        .profile-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .profile-avatar-edit {
            position: absolute;
            bottom: 0;
            right: 0;
            background-color: var(--primary);
            color: white;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: var(--transition);
            border: 2px solid white;
        }

        .profile-avatar-edit:hover {
            background-color: var(--primary-dark);
            transform: scale(1.1);
        }

        .profile-name {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 5px;
            color: white;
        }

        .profile-status {
            font-size: 0.9375rem;
            opacity: 0.9;
            margin-bottom: 15px;
            color: white;
        }

        .profile-form {
            padding: 25px;
            max-height: 60vh;
            overflow-y: auto;
        }

        .profile-form-group {
            margin-bottom: 20px;
        }

        .profile-form-label {
            display: block;
            margin-bottom: 10px;
            font-weight: 500;
            color: var(--dark);
        }

        body.dark-mode .profile-form-label {
            color: var(--dark);
        }

        .profile-form-input {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid var(--gray-light);
            border-radius: var(--border-radius);
            font-size: 1rem;
            background-color: var(--light);
            color: var(--dark);
            transition: var(--transition);
            box-shadow: var(--shadow-sm);
        }

        body.dark-mode .profile-form-input {
            background-color: #2d3436;
            border-color: #374248;
            color: var(--dark);
        }

        .profile-form-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.2);
        }

        .profile-form-actions {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            margin-top: 25px;
            position: sticky;
            bottom: 0;
            background-color: var(--light);
            padding: 15px 0;
        }

        body.dark-mode .profile-form-actions {
            background-color: #2d3436;
        }

        /* Blocked Users Section */
        .blocked-users-section {
            margin-top: 30px;
            border-top: 1px solid var(--gray-light);
            padding-top: 20px;
        }

        .blocked-users-section h4 {
            font-size: 1.1rem;
            margin-bottom: 15px;
            color: var(--dark);
        }

        .blocked-user {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid var(--gray-light);
        }

        .blocked-user-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .unblock-btn {
            background-color: var(--danger);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: var(--border-radius);
            font-size: 0.875rem;
            cursor: pointer;
            transition: var(--transition);
        }

        .unblock-btn:hover {
            background-color: #c0392b;
            transform: translateY(-2px);
        }

        /* Chat Menu Modal */
        .chat-menu-modal {
            position: fixed;
            top: 70px;
            right: 20px;
            background-color: white;
            border-radius: var(--border-radius-lg);
            box-shadow: var(--shadow-xl);
            z-index: 1000;
            display: none;
            min-width: 220px;
            overflow: hidden;
            animation: fadeInDown 0.3s ease-out;
        }

        body.dark-mode .chat-menu-modal {
            background-color: #2d3436;
        }

        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .menu-item {
            display: flex;
            align-items: center;
            padding: 12px 20px;
            width: 100%;
            background: none;
            border: none;
            text-align: left;
            cursor: pointer;
            transition: var(--transition);
            color: var(--dark);
            font-size: 0.9375rem;
        }

        body.dark-mode .menu-item {
            color: var(--dark);
        }

        .menu-item i {
            margin-right: 12px;
            width: 20px;
            text-align: center;
            font-size: 1rem;
        }

        .menu-item:hover {
            background-color: var(--gray-light);
            color: var(--primary);
        }

        body.dark-mode .menu-item:hover {
            background-color: #374248;
        }

        .menu-item.danger {
            color: var(--danger);
        }

        .menu-item.danger:hover {
            background-color: rgba(214, 48, 49, 0.1);
        }

        /* New Chat Modal */
        .contacts-list {
            margin-top: 15px;
        }

        .contact-item {
            padding: 12px 0;
            display: flex;
            align-items: center;
            gap: 15px;
            cursor: pointer;
            border-bottom: 1px solid var(--gray-light);
            transition: var(--transition);
        }

        body.dark-mode .contact-item {
            border-bottom: 1px solid #374248;
        }

        .contact-item:last-child {
            border-bottom: none;
        }

        .contact-item:hover {
            background-color: rgba(108, 92, 231, 0.05);
        }

        body.dark-mode .contact-item:hover {
            background-color: #1e272e;
        }

        .contact-name {
            font-weight: 500;
            font-size: 0.9375rem;
            color: var(--dark);
        }

        .contact-status {
            font-size: 0.75rem;
            color: var(--gray-dark);
        }

        .online {
            color: var(--success);
        }

        /* Status View */
        .status-view {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: white;
            z-index: 900;
            display: none;
            flex-direction: column;
        }

        body.dark-mode .status-view {
            background-color: #121a21;
        }

        .status-header {
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 20px;
            background-color: var(--primary);
            color: white;
        }

        .status-header h3 {
            font-size: 1.125rem;
        }

        #back-to-chats-btn {
            background: none;
            border: none;
            color: white;
            font-size: 1.25rem;
            cursor: pointer;
        }

        .status-list {
            flex: 1;
            overflow-y: auto;
            background-color: var(--light);
        }

        body.dark-mode .status-list {
            background-color: #121a21;
        }

        .status-item {
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            border-bottom: 1px solid var(--gray-light);
            cursor: pointer;
            transition: var(--transition);
        }

        body.dark-mode .status-item {
            border-bottom: 1px solid #2d3436;
        }

        .status-item:hover {
            background-color: var(--gray-light);
        }

        body.dark-mode .status-item:hover {
            background-color: #2d3436;
        }

        .status-item .avatar {
            position: relative;
        }

        .status-item .avatar::after {
            content: '';
            position: absolute;
            bottom: 0;
            right: 0;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: var(--success);
            border: 2px solid white;
        }

        .status-info {
            flex: 1;
        }

        .status-name {
            font-weight: 600;
            font-size: 0.9375rem;
            margin-bottom: 3px;
            color: var(--dark);
        }

        .status-time {
            font-size: 0.75rem;
            color: var(--gray-dark);
        }

        /* Add Status */
        .add-status {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 25px 20px;
            border-bottom: 1px solid var(--gray-light);
            cursor: pointer;
            transition: var(--transition);
        }

        body.dark-mode .add-status {
            border-bottom: 1px solid #2d3436;
        }

        .add-status:hover {
            background-color: var(--gray-light);
        }

        body.dark-mode .add-status:hover {
            background-color: #2d3436;
        }

        .add-status-avatar {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background-color: var(--gray-light);
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            margin-bottom: 15px;
            transition: var(--transition);
        }

        body.dark-mode .add-status-avatar {
            background-color: #2d3436;
        }

        .add-status-avatar i {
            font-size: 1.75rem;
            color: var(--gray-dark);
        }

        .add-status-text {
            font-size: 0.9375rem;
            color: var(--gray-dark);
            font-weight: 500;
        }

        /* Create Status Modal */
        .create-status-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }

        .status-media-preview {
            width: 100%;
            height: 300px;
            border-radius: var(--border-radius-lg);
            overflow: hidden;
            margin-bottom: 20px;
            background-color: var(--gray-light);
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }

        body.dark-mode .status-media-preview {
            background-color: #2d3436;
        }

        .status-media-preview img,
        .status-media-preview video {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .status-media-preview i {
            font-size: 3rem;
            color: var(--gray-dark);
        }

        .status-caption {
            width: 100%;
            padding: 14px 16px;
            border: 1px solid var(--gray-light);
            border-radius: var(--border-radius);
            font-size: 0.9375rem;
            margin-bottom: 20px;
            resize: none;
            background-color: var(--light);
            color: var(--dark);
            min-height: 100px;
        }

        body.dark-mode .status-caption {
            background-color: #2d3436;
            border-color: #374248;
            color: var(--dark);
        }

        .status-caption:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.2);
        }

        /* Image Preview Modal */
        .image-preview {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            padding: 20px;
        }

        .image-preview img {
            max-width: 100%;
            max-height: 70vh;
            border-radius: var(--border-radius-lg);
            box-shadow: var(--shadow-lg);
        }

        /* User Menu Modal */
        .user-menu-modal {
            position: fixed;
            top: 70px;
            right: 20px;
            background-color: white;
            border-radius: var(--border-radius-lg);
            box-shadow: var(--shadow-xl);
            z-index: 1000;
            display: none;
            min-width: 220px;
            overflow: hidden;
            animation: fadeInDown 0.3s ease-out;
        }

        body.dark-mode .user-menu-modal {
            background-color: #2d3436;
        }

        /* Video Call Modal */
        .video-call-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: var(--darker);
            z-index: 1000;
            display: none;
            flex-direction: column;
        }

        .video-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .remote-video {
            flex: 1;
            background-color: black;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .remote-video video {
            max-width: 100%;
            max-height: 100%;
        }

        .local-video {
            position: absolute;
            bottom: 20px;
            right: 20px;
            width: 150px;
            height: 200px;
            background-color: black;
            border-radius: var(--border-radius);
            overflow: hidden;
            box-shadow: var(--shadow-lg);
        }

        .local-video video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .call-controls {
            padding: 20px;
            display: flex;
            justify-content: center;
            gap: 30px;
            background-color: rgba(0, 0, 0, 0.7);
        }

        .call-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: var(--transition);
            box-shadow: var(--shadow-md);
        }

        .end-call {
            background-color: var(--danger);
        }

        .mute-call,
        .video-toggle {
            background-color: rgba(255, 255, 255, 0.2);
        }

        .call-btn:hover {
            transform: scale(1.1);
        }

        .call-btn i {
            font-size: 1.5rem;
            color: white;
        }

        /* User Status Posts Modal - Enhanced */
        .user-posts-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: black;
            z-index: 1000;
            display: none;
            flex-direction: column;
        }

        .posts-header {
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            z-index: 1;
        }

        .posts-header h3 {
            font-size: 1rem;
        }

        .posts-container {
            flex: 1;
            display: flex;
            overflow: hidden;
            scroll-snap-type: x mandatory;
            scroll-behavior: smooth;
            position: relative;
        }

        .post-item {
            min-width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            scroll-snap-align: start;
            position: relative;
            flex-shrink: 0;
        }

        .post-item img {
            max-width: 100%;
            max-height: 100%;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }

        .post-item video {
            max-width: 100%;
            max-height: 100%;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }

        .post-caption {
            position: absolute;
            bottom: 80px;
            left: 0;
            right: 0;
            text-align: center;
            color: white;
            padding: 10px 20px;
            background-color: rgba(0, 0, 0, 0.5);
        }

        .post-actions {
            position: absolute;
            bottom: 20px;
            left: 0;
            right: 0;
            display: flex;
            justify-content: center;
            gap: 20px;
            z-index: 2;
        }

        .post-action {
            background-color: rgba(0, 0, 0, 0.5);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: var(--transition);
        }

        .post-action:hover {
            background-color: rgba(255, 255, 255, 0.2);
            transform: scale(1.1);
        }

        /* Enhanced Comment Section */
        .comment-section {
            position: absolute;
            right: 0;
            top: 0;
            bottom: 0;
            width: 350px;
            background-color: rgba(255, 255, 255, 0.9);
            z-index: 2;
            display: none;
            flex-direction: column;
            border-left: 1px solid rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        body.dark-mode .comment-section {
            background-color: rgba(30, 41, 59, 0.95);
            border-left: 1px solid rgba(0, 0, 0, 0.3);
        }

        .comment-header {
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }

        body.dark-mode .comment-header {
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .comment-header h4 {
            font-size: 1rem;
            color: var(--dark);
        }

        body.dark-mode .comment-header h4 {
            color: #dfe6e9;
        }

        .close-comments {
            background: none;
            border: none;
            color: var(--gray-dark);
            font-size: 1.25rem;
            cursor: pointer;
        }

        .comments-list {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
        }

        .comment {
            margin-bottom: 12px;
            padding: 12px;
            background-color: rgba(255, 255, 255, 0.8);
            border-radius: var(--border-radius);
            font-size: 0.875rem;
            box-shadow: var(--shadow-sm);
        }

        body.dark-mode .comment {
            background-color: rgba(45, 52, 54, 0.8);
        }

        .comment-user {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 5px;
        }

        .comment-user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            overflow: hidden;
        }

        .comment-user-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .comment-user-name {
            font-weight: bold;
            color: var(--primary);
        }

        body.dark-mode .comment-user-name {
            color: var(--primary-light);
        }

        .comment-text {
            word-break: break-word;
            margin-top: 5px;
            color: var(--dark);
        }

        body.dark-mode .comment-text {
            color: #dfe6e9;
        }

        .comment-time {
            font-size: 0.75rem;
            color: var(--gray);
            margin-top: 5px;
            text-align: right;
        }

        .comment-input-area {
            padding: 15px;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
            background-color: var(--light);
        }

        body.dark-mode .comment-input-area {
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            background-color: #2d3436;
        }

        .comment-input-container {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        #comment-input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid var(--gray-light);
            border-radius: var(--border-radius-lg);
            font-size: 0.9375rem;
            resize: none;
            max-height: 100px;
            background-color: var(--light);
            color: var(--dark);
        }

        body.dark-mode #comment-input {
            background-color: #2d3436;
            border-color: #374248;
            color: #dfe6e9;
        }

        #comment-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(108, 92, 231, 0.2);
        }

        #submit-comment {
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: var(--border-radius);
            padding: 12px 16px;
            cursor: pointer;
            transition: var(--transition);
        }

        #submit-comment:hover {
            background-color: var(--primary-dark);
        }

        .likes-count {
            position: absolute;
            top: 70px;
            left: 20px;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 5px 10px;
            border-radius: var(--border-radius);
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .likes-count i {
            color: var(--danger);
        }

        .views-count {
            position: absolute;
            top: 70px;
            right: 20px;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 5px 10px;
            border-radius: var(--border-radius);
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        /* Status Navigation Dots */
        .status-dots {
            position: absolute;
            bottom: 90px;
            left: 0;
            right: 0;
            display: flex;
            justify-content: center;
            gap: 8px;
            z-index: 1;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--status-dot-inactive);
            cursor: pointer;
            transition: var(--transition);
        }

        .status-dot.active {
            background-color: var(--status-dot-active);
            transform: scale(1.2);
        }

        .post-nav {
            position: absolute;
            top: 0;
            bottom: 0;
            width: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 2rem;
            cursor: pointer;
            z-index: 1;
            opacity: 0.5;
            transition: var(--transition);
        }

        .post-nav:hover {
            opacity: 1;
            background-color: rgba(0, 0, 0, 0.3);
        }

        .post-prev {
            left: 0;
        }

        .post-next {
            right: 0;
        }

        /* Group Creation Modal */
        .group-creation-modal {
            max-width: 500px;
        }

        .group-form {
            padding: 20px;
        }

        .group-avatar {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            margin: 0 auto 20px;
            overflow: hidden;
            background-color: var(--gray-light);
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            cursor: pointer;
        }

        .group-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .group-avatar i {
            font-size: 2rem;
            color: var(--gray-dark);
        }

        #group-avatar-input {
            display: none;
        }

        .group-members {
            max-height: 200px;
            overflow-y: auto;
            margin: 15px 0;
            border: 1px solid var(--gray-light);
            border-radius: var(--border-radius);
            padding: 10px;
        }

        .group-member-item {
            display: flex;
            align-items: center;
            padding: 8px;
            border-bottom: 1px solid var(--gray-light);
        }

        .group-member-item:last-child {
            border-bottom: none;
        }

        .group-member-checkbox {
            margin-right: 10px;
        }

        /* Group Management Modal */
        .group-management-modal {
            max-width: 500px;
        }

        .group-info {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
        }

        .group-members-list {
            max-height: 300px;
            overflow-y: auto;
        }

        .group-member {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid var(--gray-light);
        }

        .group-member-actions {
            display: flex;
            gap: 10px;
        }

        .make-admin-btn, .remove-member-btn {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 0.875rem;
        }

        .make-admin-btn {
            color: var(--primary);
        }

        .remove-member-btn {
            color: var(--danger);
        }

        .admin-badge {
            background-color: var(--primary);
            color: white;
            padding: 2px 6px;
            border-radius: var(--border-radius);
            font-size: 0.75rem;
        }

        /* Responsive Styles */
        @media (max-width: 768px) {
            .sidebar {
                width: 100%;
                position: absolute;
                top: 0;
                left: 0;
                z-index: 20;
                transform: translateX(0);
                transition: var(--transition);
            }

            .sidebar.hidden {
                transform: translateX(-100%);
            }

            .chat-area {
                display: none;
            }

            .chat-area.active {
                display: flex;
            }

            .status-view {
                display: none;
            }

            .status-view.active {
                display: flex;
            }

            .back-to-chats {
                display: block;
            }

            .message {
                max-width: 85%;
            }

            .comment-section {
                width: 100%;
                bottom: 0;
                height: 50%;
                border-left: none;
                border-top: 1px solid rgba(0, 0, 0, 0.1);
            }

            body.dark-mode .comment-section {
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }

            .modal-content {
                width: 95%;
            }
        }

        /* Animations */
        @keyframes pulse {
            0% {
                transform: scale(1);
            }

            50% {
                transform: scale(1.05);
            }

            100% {
                transform: scale(1);
            }
        }

        .pulse {
            animation: pulse 1.5s infinite;
        }

        /* Utility Classes */
        .hidden {
            display: none !important;
        }

        .text-primary {
            color: var(--primary);
        }

        .text-danger {
            color: var(--danger);
        }

        .text-success {
            color: var(--success);
        }

        .text-warning {
            color: var(--warning);
        }

        .text-info {
            color: var(--info);
        }

        .text-gray {
            color: var(--gray);
        }

        .bg-primary {
            background-color: var(--primary);
        }

        .bg-danger {
            background-color: var(--danger);
        }

        .bg-success {
            background-color: var(--success);
        }

        .bg-warning {
            background-color: var(--warning);
        }

        .bg-info {
            background-color: var(--info);
        }

        .bg-gray {
            background-color: var(--gray);
        }

        .rounded {
            border-radius: var(--border-radius);
        }

        .rounded-lg {
            border-radius: var(--border-radius-lg);
        }

        .rounded-xl {
            border-radius: var(--border-radius-xl);
        }

        .rounded-full {
            border-radius: 9999px;
        }

        .shadow {
            box-shadow: var(--shadow);
        }

        .shadow-md {
            box-shadow: var(--shadow-md);
        }

        .shadow-lg {
            box-shadow: var(--shadow-lg);
        }

        .shadow-xl {
            box-shadow: var(--shadow-xl);
        }

        .transition {
            transition: var(--transition);
        }

        .transition-slow {
            transition: var(--transition-slow);
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--gray-light);
            border-radius: 10px;
        }

        body.dark-mode ::-webkit-scrollbar-track {
            background: #2d3436;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--gray);
            border-radius: 10px;
        }

        body.dark-mode ::-webkit-scrollbar-thumb {
            background: #b2bec3;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--gray-dark);
        }

        /* Hide scrollbar for status posts */
        .posts-container::-webkit-scrollbar {
            display: none;
        }

        .posts-container {
            -ms-overflow-style: none;
            scrollbar-width: none;
        }
    </style>
</head>

<body>
    <!-- Auth Container -->
    <div id="auth-container" class="auth-container">
        <div class="auth-card">
            <div class="auth-header">
                <div class="auth-logo">
                    <i class="fas fa-comments"></i>
                </div>
                <h1 class="auth-title">NexaChat</h1>
                <p class="auth-subtitle">Next Generation Messaging</p>
            </div>

            <form id="login-form" class="auth-form active">
                <div class="form-group">
                    <label for="login-email" class="form-label">Email Address</label>
                    <input type="email" id="login-email" class="form-control" placeholder="your@email.com" required>
                </div>
                <div class="form-group">
                    <label for="login-password" class="form-label">Password</label>
                    <input type="password" id="login-password" class="form-control" placeholder="Password" required>
                </div>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-sign-in-alt"></i> Log In
                </button>
                <div class="auth-footer">
                    <p>Don't have an account? <a href="#" id="switch-to-register">Sign up</a></p>
                </div>
            </form>

            <form id="register-form" class="auth-form">
                <div class="form-group">
                    <label for="register-name" class="form-label">Full Name</label>
                    <input type="text" id="register-name" class="form-control" placeholder="Your name" required>
                </div>
                <div class="form-group">
                    <label for="register-email" class="form-label">Email Address</label>
                    <input type="email" id="register-email" class="form-control" placeholder="your@email.com" required>
                </div>
                <div class="form-group">
                    <label for="register-password" class="form-label">Password</label>
                    <input type="password" id="register-password" class="form-control" placeholder="Password" required>
                </div>
                <div class="form-group">
                    <label for="register-avatar" class="form-label">Profile Picture</label>
                    <div class="avatar-upload">
                        <div class="avatar avatar-md" id="avatar-preview">
                            <i class="fas fa-user"></i>
                        </div>
                        <input type="file" id="register-avatar" accept="image/*" style="display: none;">
                        <button type="button" class="btn btn-outline" id="upload-avatar-btn">
                            <i class="fas fa-upload"></i> Choose Image
                        </button>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-user-plus"></i> Create Account
                </button>
                <div class="auth-footer">
                    <p>Already have an account? <a href="#" id="switch-to-login">Log in</a></p>
                </div>
            </form>
        </div>
    </div>

    <!-- App Container -->
    <div id="app-container" class="app-container">
        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <!-- Header -->
            <div class="sidebar-header">
                <div class="user-profile">
                    <div class="avatar" id="current-user-avatar">
                        <img src="" alt="Profile" id="current-user-avatar-img">
                    </div>
                    <div class="user-info">
                        <span class="user-name" id="current-user-name"></span>
                        <span class="user-status" id="current-user-status">
                            <span class="status-dot"></span> Online
                        </span>
                    </div>
                </div>
                <div class="sidebar-actions">
                    <button id="status-btn" title="Status">
                        <i class="fas fa-feather"></i>
                    </button>
                    <button id="new-chat-btn" title="New Chat">
                        <i class="fas fa-comment-medical"></i>
                    </button>
                    <button id="new-group-btn" title="New Group">
                        <i class="fas fa-users"></i>
                    </button>
                    <button id="menu-btn" title="Menu">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                </div>
            </div>

            <!-- Search -->
            <div class="search-bar">
                <div class="search-container">
                    <i class="fas fa-search search-icon"></i>
                    <input type="text" id="search-users" placeholder="Search or start new chat">
                </div>
            </div>

            <!-- Users List -->
            <div class="users-list" id="users-list">
                <!-- Users will be dynamically inserted here -->
            </div>

            <!-- Chats List -->
            <div class="chats-list" id="chats-list">
                <!-- Chats will be dynamically inserted here -->
            </div>
        </div>

        <!-- Chat Area -->
        <div class="chat-area" id="chat-area">
            <!-- Default screen when no chat selected -->
            <div class="empty-chat" id="empty-chat">
                <div class="empty-content">
                    <img src="https://cdn-icons-png.flaticon.com/512/2462/2462719.png" alt="Start chatting">
                    <h2>NexaChat</h2>
                    <p>Send and receive messages with end-to-end encryption</p>
                    <p>Connect with your friends across multiple devices</p>
                </div>
            </div>

            <!-- Active chat header -->
            <div class="chat-header" id="chat-header">
                <div class="chat-user">
                    <button class="back-to-chats" id="back-to-chats-btn">
                        <i class="fas fa-arrow-left"></i>
                    </button>
                    <div class="avatar">
                        <img src="" alt="Contact" id="chat-contact-avatar">
                    </div>
                    <div class="user-info">
                        <span id="chat-contact-name"></span>
                        <span id="chat-contact-status">
                            <span class="status-dot"></span> Online
                        </span>
                    </div>
                </div>
                <div class="chat-actions">
                    <button id="voice-call-btn" title="Voice Call">
                        <i class="fas fa-phone"></i>
                    </button>
                    <button id="video-call-btn" title="Video Call">
                        <i class="fas fa-video"></i>
                    </button>
                    <button id="chat-menu-btn" title="Menu">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                </div>
            </div>

            <!-- Messages container -->
            <div class="messages-container" id="messages-container">
                <!-- Messages will be dynamically inserted here -->
            </div>

            <!-- Message input -->
            <div class="message-input" id="message-input-container">
                <div class="input-actions">
                    <button id="emoji-btn" title="Emoji">
                        <i class="far fa-smile"></i>
                    </button>
                    <button id="attach-btn" title="Attach">
                        <i class="fas fa-paperclip"></i>
                    </button>
                    <input type="file" id="file-input" accept="image/*, video/*, audio/*, .pdf, .doc, .docx">
                </div>
                <textarea id="message-input" placeholder="Type a message" rows="1"></textarea>
                <button id="send-btn" title="Send">
                    <i class="fas fa-paper-plane"></i>
                </button>
                <button id="voice-message-btn" title="Record Voice">
                    <i class="fas fa-microphone"></i>
                </button>
                <div class="emoji-picker-container" id="emoji-picker-container">
                    <emoji-picker></emoji-picker>
                </div>
            </div>
        </div>

        <!-- Status View -->
        <div class="status-view" id="status-view">
            <div class="status-header">
                <button id="back-to-chats-btn">
                    <i class="fas fa-arrow-left"></i>
                </button>
                <h3>Moments</h3>
            </div>
            <div class="status-list">
                <div class="add-status" id="add-status">
                    <div class="add-status-avatar">
                        <i class="fas fa-plus"></i>
                    </div>
                    <div class="add-status-text">Create New Moment</div>
                </div>
                <!-- Status updates will be dynamically inserted here -->
            </div>
        </div>

        <!-- New Chat Modal -->
        <div class="modal" id="new-chat-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>New Chat</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="search-container">
                        <i class="fas fa-search search-icon"></i>
                        <input type="text" id="search-contacts" placeholder="Search contacts">
                    </div>
                    <div class="contacts-list" id="contacts-list">
                        <!-- Contacts will be dynamically inserted here -->
                    </div>
                </div>
            </div>
        </div>

        <!-- New Group Modal -->
        <div class="modal" id="new-group-modal">
            <div class="modal-content group-creation-modal">
                <div class="modal-header">
                    <h3>Create New Group</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="group-form">
                        <div class="group-avatar" id="group-avatar">
                            <i class="fas fa-camera"></i>
                            <input type="file" id="group-avatar-input" accept="image/*">
                        </div>
                        <div class="form-group">
                            <label for="group-name" class="form-label">Group Name</label>
                            <input type="text" id="group-name" class="form-control" placeholder="Enter group name" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Add Members</label>
                            <div class="group-members" id="group-members-list">
                                <!-- Members will be added here -->
                            </div>
                        </div>
                        <button class="btn btn-primary" id="create-group-btn">
                            <i class="fas fa-users"></i> Create Group
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Group Management Modal -->
        <div class="modal" id="group-management-modal">
            <div class="modal-content group-management-modal">
                <div class="modal-header">
                    <h3 id="group-management-title">Manage Group</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="group-info">
                        <div class="avatar avatar-lg" id="group-management-avatar">
                            <img src="" alt="Group Avatar">
                        </div>
                        <div>
                            <h4 id="group-management-name"></h4>
                            <div id="group-management-members-count"></div>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="group-name-input" class="form-label">Group Name</label>
                        <input type="text" id="group-name-input" class="form-control">
                    </div>

                    <div class="form-group">
                        <label class="form-label">Change Group Photo</label>
                        <input type="file" id="group-photo-input" accept="image/*" class="form-control">
                    </div>

                    <h4>Group Members</h4>
                    <div class="group-members-list" id="group-management-members">
                        <!-- Members will be listed here -->
                    </div>

                    <div class="profile-form-actions">
                        <button class="btn btn-outline" id="cancel-group-management-btn">Cancel</button>
                        <button class="btn btn-primary" id="save-group-changes-btn">Save Changes</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Profile Modal -->
        <div class="modal" id="profile-modal">
            <div class="modal-content profile-modal">
                <div class="profile-header">
                    <div class="profile-avatar" id="profile-avatar">
                        <img src="" alt="Profile" id="profile-avatar-img">
                        <div class="profile-avatar-edit" id="profile-avatar-edit">
                            <i class="fas fa-camera"></i>
                        </div>
                        <input type="file" id="profile-avatar-input" accept="image/*" style="display: none;">
                    </div>
                    <h2 class="profile-name" id="profile-name"></h2>
                    <p class="profile-status" id="profile-status"></p>
                </div>
                <div class="profile-form">
                    <div class="profile-form-group">
                        <label for="profile-name-input" class="profile-form-label">Full Name</label>
                        <input type="text" id="profile-name-input" class="profile-form-input">
                    </div>
                    <div class="profile-form-group">
                        <label for="profile-email" class="profile-form-label">Email Address</label>
                        <input type="email" id="profile-email" class="profile-form-input">
                    </div>
                    <div class="profile-form-group">
                        <label for="profile-password" class="profile-form-label">Password (leave blank to keep current)</label>
                        <input type="password" id="profile-password" class="profile-form-input" placeholder="New password">
                    </div>
                    <div class="profile-form-group">
                        <label for="profile-status-input" class="profile-form-label">Status</label>
                        <input type="text" id="profile-status-input" class="profile-form-input" placeholder="Your status">
                    </div>

                    <!-- Blocked Users Section -->
                    <div class="blocked-users-section">
                        <h4>Blocked Users</h4>
                        <div id="blocked-users-list">
                            <!-- Blocked users will be inserted here -->
                        </div>
                    </div>

                    <div class="profile-form-actions">
                        <button class="btn btn-outline" id="cancel-profile-btn">Cancel</button>
                        <button class="btn btn-primary" id="save-profile-btn">Save Changes</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Status Modal -->
        <div class="modal" id="create-status-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Create Moment</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="create-status-container">
                        <div class="status-media-preview" id="status-media-preview">
                            <i class="fas fa-camera"></i>
                        </div>
                        <input type="file" id="status-media-input" accept="image/*, video/*">
                        <button class="btn btn-primary" id="select-status-media">
                            <i class="fas fa-image"></i> Select Photo/Video
                        </button>
                        <textarea class="status-caption" placeholder="Add a caption..." id="status-caption"></textarea>
                        <button class="btn btn-primary" id="post-status-btn">
                            <i class="fas fa-share"></i> Post Moment
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Image Preview Modal -->
        <div class="modal" id="image-preview-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Photo</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="image-preview">
                        <img src="" alt="Preview" id="image-preview-img">
                    </div>
                </div>
            </div>
        </div>

        <!-- Chat Menu Modal -->
        <div class="modal chat-menu-modal" id="chat-menu-modal">
            <button class="menu-item" id="block-user-btn">
                <i class="fas fa-ban"></i> Block User
            </button>
            <button class="menu-item" id="manage-group-btn" style="display: none;">
                <i class="fas fa-cog"></i> Manage Group
            </button>
            <button class="menu-item danger" id="delete-chat-btn">
                <i class="fas fa-trash"></i> Delete Conversation
            </button>
        </div>

        <!-- User Posts Modal - Enhanced -->
        <div class="modal user-posts-modal" id="user-posts-modal">
            <div class="posts-header">
                <div class="user-profile">
                    <div class="avatar avatar-sm">
                        <img src="" alt="Profile" id="posts-user-avatar">
                    </div>
                    <div class="user-info">
                        <span id="posts-user-name"></span>
                    </div>
                </div>
                <button class="close-modal">&times;</button>
            </div>
            <div class="posts-container" id="posts-container">
                <!-- Posts will be dynamically inserted here -->
            </div>
            <div class="status-dots" id="status-dots">
                <!-- Status dots will be dynamically inserted here -->
            </div>
            <div class="likes-count" id="likes-count">
                <i class="fas fa-heart"></i> <span id="likes-count-text">0</span>
            </div>
            <div class="views-count" id="views-count">
                <i class="fas fa-eye"></i> <span id="views-count-text">0</span>
            </div>
            <div class="post-actions">
                <button class="post-action" id="like-post-btn">
                    <i class="fas fa-heart"></i>
                </button>
                <button class="post-action" id="comment-post-btn">
                    <i class="fas fa-comment"></i>
                </button>
                <button class="post-action" id="share-post-btn">
                    <i class="fas fa-share"></i>
                </button>
            </div>
            <div class="post-nav post-prev" id="post-prev">
                <i class="fas fa-chevron-left"></i>
            </div>
            <div class="post-nav post-next" id="post-next">
                <i class="fas fa-chevron-right"></i>
            </div>

            <!-- Enhanced Comment Section -->
            <div class="comment-section" id="comment-section">
                <div class="comment-header">
                    <h4>Comments</h4>
                    <button class="close-comments" id="close-comments-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="comments-list" id="comments-list">
                    <!-- Comments will be dynamically inserted here -->
                </div>
                <div class="comment-input-area">
                    <div class="comment-input-container">
                        <textarea id="comment-input" placeholder="Add a comment..." rows="1"></textarea>
                        <button id="submit-comment">Post</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Video Call Modal -->
        <div class="video-call-modal" id="video-call-modal">
            <div class="video-container">
                <div class="remote-video" id="remote-video">
                    <video id="remote-stream" autoplay playsinline></video>
                </div>
                <div class="local-video" id="local-video">
                    <video id="local-stream" autoplay playsinline muted></video>
                </div>
            </div>
            <div class="call-controls">
                <div class="call-btn mute-call" id="mute-call-btn">
                    <i class="fas fa-microphone"></i>
                </div>
                <div class="call-btn end-call" id="end-call-btn">
                    <i class="fas fa-phone"></i>
                </div>
                <div class="call-btn video-toggle" id="video-toggle-btn">
                    <i class="fas fa-video"></i>
                </div>
            </div>
        </div>

        <!-- User Menu -->
        <div class="user-menu-modal" id="user-menu-modal">
            <button class="menu-item" id="profile-btn">
                <i class="fas fa-user"></i> Profile
            </button>
            <button class="menu-item" id="toggle-dark-mode">
                <i class="fas fa-moon"></i> Dark Mode
            </button>
            <button class="menu-item" id="logout-btn">
                <i class="fas fa-sign-out-alt"></i> Log Out
            </button>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/emoji-picker-element@1.12.0/dist/index.min.js"></script>
    <script>
        // DOM Elements
        const authContainer = document.getElementById('auth-container');
        const appContainer = document.getElementById('app-container');
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        const switchToRegister = document.getElementById('switch-to-register');
        const switchToLogin = document.getElementById('switch-to-login');
        const uploadAvatarBtn = document.getElementById('upload-avatar-btn');
        const registerAvatar = document.getElementById('register-avatar');
        const avatarPreview = document.getElementById('avatar-preview');
        const currentUserName = document.getElementById('current-user-name');
        const currentUserAvatar = document.getElementById('current-user-avatar-img');
        const currentUserStatus = document.getElementById('current-user-status');
        const searchUsersInput = document.getElementById('search-users');
        const usersList = document.getElementById('users-list');
        const chatsList = document.getElementById('chats-list');
        const chatArea = document.getElementById('chat-area');
        const emptyChat = document.getElementById('empty-chat');
        const chatHeader = document.getElementById('chat-header');
        const messagesContainer = document.getElementById('messages-container');
        const messageInput = document.getElementById('message-input');
        const messageInputContainer = document.getElementById('message-input-container');
        const sendBtn = document.getElementById('send-btn');
        const voiceMessageBtn = document.getElementById('voice-message-btn');
        const emojiBtn = document.getElementById('emoji-btn');
        const emojiPickerContainer = document.getElementById('emoji-picker-container');
        const attachBtn = document.getElementById('attach-btn');
        const fileInput = document.getElementById('file-input');
        const newChatBtn = document.getElementById('new-chat-btn');
        const newGroupBtn = document.getElementById('new-group-btn');
        const newChatModal = document.getElementById('new-chat-modal');
        const newGroupModal = document.getElementById('new-group-modal');
        const groupManagementModal = document.getElementById('group-management-modal');
        const searchContactsInput = document.getElementById('search-contacts');
        const contactsList = document.getElementById('contacts-list');
        const closeModals = document.querySelectorAll('.close-modal');
        const statusBtn = document.getElementById('status-btn');
        const statusView = document.getElementById('status-view');
        const backToChatsBtn = document.getElementById('back-to-chats-btn');
        const addStatusBtn = document.getElementById('add-status');
        const createStatusModal = document.getElementById('create-status-modal');
        const selectStatusMediaBtn = document.getElementById('select-status-media');
        const statusMediaInput = document.getElementById('status-media-input');
        const statusMediaPreview = document.getElementById('status-media-preview');
        const statusCaption = document.getElementById('status-caption');
        const postStatusBtn = document.getElementById('post-status-btn');
        const logoutBtn = document.getElementById('logout-btn');
        const userMenuBtn = document.getElementById('menu-btn');
        const userMenuModal = document.getElementById('user-menu-modal');
        const chatMenuBtn = document.getElementById('chat-menu-btn');
        const chatMenuModal = document.getElementById('chat-menu-modal');
        const blockUserBtn = document.getElementById('block-user-btn');
        const manageGroupBtn = document.getElementById('manage-group-btn');
        const deleteChatBtn = document.getElementById('delete-chat-btn');
        const imagePreviewModal = document.getElementById('image-preview-modal');
        const imagePreviewImg = document.getElementById('image-preview-img');
        const toggleDarkModeBtn = document.getElementById('toggle-dark-mode');
        const userPostsModal = document.getElementById('user-posts-modal');
        const postsContainer = document.getElementById('posts-container');
        const postsUserName = document.getElementById('posts-user-name');
        const postsUserAvatar = document.getElementById('posts-user-avatar');
        const likePostBtn = document.getElementById('like-post-btn');
        const likesCount = document.getElementById('likes-count');
        const likesCountText = document.getElementById('likes-count-text');
        const viewsCount = document.getElementById('views-count');
        const viewsCountText = document.getElementById('views-count-text');
        const commentPostBtn = document.getElementById('comment-post-btn');
        const sharePostBtn = document.getElementById('share-post-btn');
        const postComments = document.getElementById('comments-list');
        const postPrev = document.getElementById('post-prev');
        const postNext = document.getElementById('post-next');
        const videoCallModal = document.getElementById('video-call-modal');
        const remoteVideo = document.getElementById('remote-stream');
        const localVideo = document.getElementById('local-stream');
        const muteCallBtn = document.getElementById('mute-call-btn');
        const endCallBtn = document.getElementById('end-call-btn');
        const videoToggleBtn = document.getElementById('video-toggle-btn');
        const voiceCallBtn = document.getElementById('voice-call-btn');
        const videoCallBtn = document.getElementById('video-call-btn');
        const profileModal = document.getElementById('profile-modal');
        const profileBtn = document.getElementById('profile-btn');
        const profileAvatarImg = document.getElementById('profile-avatar-img');
        const profileAvatarEdit = document.getElementById('profile-avatar-edit');
        const profileAvatarInput = document.getElementById('profile-avatar-input');
        const profileName = document.getElementById('profile-name');
        const profileStatus = document.getElementById('profile-status');
        const profileNameInput = document.getElementById('profile-name-input');
        const profileEmail = document.getElementById('profile-email');
        const profilePassword = document.getElementById('profile-password');
        const profileStatusInput = document.getElementById('profile-status-input');
        const cancelProfileBtn = document.getElementById('cancel-profile-btn');
        const saveProfileBtn = document.getElementById('save-profile-btn');
        const backToChatsBtnMobile = document.getElementById('back-to-chats-btn');
        const blockedUsersList = document.getElementById('blocked-users-list');
        const commentSection = document.getElementById('comment-section');
        const closeCommentsBtn = document.getElementById('close-comments-btn');
        const commentsList = document.getElementById('comments-list');
        const commentInput = document.getElementById('comment-input');
        const submitCommentBtn = document.getElementById('submit-comment');
        const statusDots = document.getElementById('status-dots');
        const groupAvatar = document.getElementById('group-avatar');
        const groupAvatarInput = document.getElementById('group-avatar-input');
        const groupName = document.getElementById('group-name');
        const groupMembersList = document.getElementById('group-members-list');
        const createGroupBtn = document.getElementById('create-group-btn');
        const groupManagementTitle = document.getElementById('group-management-title');
        const groupManagementAvatar = document.getElementById('group-management-avatar');
        const groupManagementName = document.getElementById('group-management-name');
        const groupManagementMembersCount = document.getElementById('group-management-members-count');
        const groupNameInput = document.getElementById('group-name-input');
        const groupPhotoInput = document.getElementById('group-photo-input');
        const groupManagementMembers = document.getElementById('group-management-members');
        const cancelGroupManagementBtn = document.getElementById('cancel-group-management-btn');
        const saveGroupChangesBtn = document.getElementById('save-group-changes-btn');

        // State
        let currentUser = null;
        let users = []; // All registered users
        let contacts = []; // User's contacts
        let chats = []; // User's chats
        let groups = []; // User's groups
        let statusUpdates = []; // All status updates
        let currentChat = null;
        let isDarkMode = false;
        let isMuted = false;
        let isVideoOff = false;
        let localStream = null;
        let peerConnection = null;
        let currentPostsUser = null;
        let currentPostIndex = 0;
        let blockedUsers = []; // Users blocked by current user
        let emojiPicker = null;
        let socket = null; // For real-time communication
        let typingTimeout = null;
        let touchStartX = 0;
        let touchEndX = 0;
        let selectedGroupMembers = []; // For group creation
        let currentManagedGroup = null; // For group management

        // API Base URL
        const API_BASE = window.location.origin;

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            loadData();
            initEventListeners();
            initSocketConnection();
            // Initialize emoji picker
            emojiPicker = document.querySelector('emoji-picker');

            // Create a custom emoji panel with categorized tabs
            function createCustomEmojiPanel() {
                const customEmojiPanel = document.createElement('div');
                customEmojiPanel.className = 'custom-emoji-panel';
                customEmojiPanel.style.display = 'none';
                customEmojiPanel.style.position = 'fixed';
                customEmojiPanel.style.bottom = '70px';
                customEmojiPanel.style.left = '20px';
                customEmojiPanel.style.background = 'white';
                customEmojiPanel.style.border = '1px solid #ccc';
                customEmojiPanel.style.borderRadius = '12px';
                customEmojiPanel.style.padding = '10px';
                customEmojiPanel.style.zIndex = '1000';
                customEmojiPanel.style.width = '420px';
                customEmojiPanel.style.maxHeight = '400px';
                customEmojiPanel.style.overflow = 'hidden';
                customEmojiPanel.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)';
                customEmojiPanel.style.display = 'flex';
                customEmojiPanel.style.flexDirection = 'column';

                // Create header with close button
                const panelHeader = document.createElement('div');
                panelHeader.style.display = 'flex';
                panelHeader.style.justifyContent = 'space-between';
                panelHeader.style.alignItems = 'center';
                panelHeader.style.marginBottom = '10px';
                panelHeader.style.paddingBottom = '5px';
                panelHeader.style.borderBottom = '2px solid #f0f0f0';

                const panelTitle = document.createElement('span');
                panelTitle.textContent = 'Emojis';
                panelTitle.style.fontWeight = 'bold';
                panelTitle.style.fontSize = '14px';
                panelTitle.style.color = '#333';

                const closeButton = document.createElement('button');
                closeButton.innerHTML = '&times;'; // X symbol
                closeButton.className = 'emoji-panel-close';
                closeButton.style.background = 'none';
                closeButton.style.border = 'none';
                closeButton.style.fontSize = '20px';
                closeButton.style.cursor = 'pointer';
                closeButton.style.padding = '0';
                closeButton.style.width = '24px';
                closeButton.style.height = '24px';
                closeButton.style.borderRadius = '50%';
                closeButton.style.display = 'flex';
                closeButton.style.alignItems = 'center';
                closeButton.style.justifyContent = 'center';
                closeButton.style.transition = 'all 0.2s ease';
                closeButton.style.color = '#666';

                closeButton.addEventListener('mouseover', () => {
                    closeButton.style.backgroundColor = '#ff4444';
                    closeButton.style.color = 'white';
                    closeButton.style.transform = 'scale(1.1)';
                });

                closeButton.addEventListener('mouseout', () => {
                    closeButton.style.backgroundColor = 'transparent';
                    closeButton.style.color = '#666';
                    closeButton.style.transform = 'scale(1)';
                });

                closeButton.addEventListener('click', () => {
                    customEmojiPanel.style.display = 'none';
                    // Save the closed state
                    localStorage.setItem('emojiPanelClosed', 'true');
                });

                panelHeader.appendChild(panelTitle);
                panelHeader.appendChild(closeButton);

                // Create tabs container
                const tabsContainer = document.createElement('div');
                tabsContainer.className = 'emoji-tabs';
                tabsContainer.style.display = 'flex';
                tabsContainer.style.flexWrap = 'wrap';
                tabsContainer.style.gap = '5px';
                tabsContainer.style.marginBottom = '10px';

                // Create emoji content area
                const emojiContent = document.createElement('div');
                emojiContent.className = 'emoji-content';
                emojiContent.style.flex = '1';
                emojiContent.style.overflowY = 'auto';
                emojiContent.style.display = 'grid';
                emojiContent.style.gridTemplateColumns = 'repeat(10, 1fr)';
                emojiContent.style.gap = '5px';
                emojiContent.style.paddingRight = '5px';

                // Add scrollbar styling
                emojiContent.style.scrollbarWidth = 'thin';
                emojiContent.style.scrollbarColor = '#ccc transparent';

                // Emoji categories with labels (your existing categories here)
                const emojiCategories = [
                    {
                        name: 'smileys',
                        label: '😊',
                        title: 'Smileys & Emotions',
                        emojis: ['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩', '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣', '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥', '😓', '🫣', '🤗', '🫡', '🤔', '🫢', '🤭', '🤫', '🤥', '😶', '🫠', '😐', '🫤', '😑', '😬', '🙄', '😯', '😦', '😧', '😮', '😲', '🥱', '😴', '🤤', '😪', '😵', '🫥', '🤐', '🥴', '🤢', '🤮', '🤧', '😷', '🤒', '🤕', '🤑', '🤠', '😈', '👿', '👹', '👺', '🤡', '💩', '👻', '💀', '☠️', '👽', '👾', '🤖', '🎃',
                        // Additional smileys
                        '🥲', '🥹', '🫨', '😶‍🌫️', '😮‍💨', '🙃', '🙂‍↔️', '🙂‍↕️', '🤭', '🤗', '🫢', '🫣', '🫠', '🫥', '🫤', '🤥', '😵‍💫', '😵', '🥴',]
                    },
                    {
                        name: 'animals',
                        label: '🐾',
                        title: 'Animals & Nature',
                        emojis: ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵', '🐔', '🐧', '🐦', '🐤', '🦄', '🦅', '🦉', '🦇', '🐺', '🐗', '🐴', '🦄', '🐝', '🐛', '🦋', '🐌', '🐞', '🐜', '🦟', '🦗', '🕷️', '🦂', '🐢', '🐍', '🦎', '🦖', '🦕', '🐙', '🦑', '🦐', '🦞', '🦀', '🐡', '🐠', '🐟', '🐬', '🐳', '🐋', '🦈', '🐊', '🐅', '🐆', '🦓', '🦍', '🦧', '🦣', '🐘', '🦛', '🦏', '🐪', '🐫', '🦒', '🦘', '🐃', '🐂', '🐄', '🐎', '🐖', '🐏', '🐑', '🦙', '🐐', '🦌', '🐕', '🐩', '🦮', '🐕‍🦺', '🐈', '🐈‍⬛', '🐓', '🦃', '🦚', '🦜', '🦢', '🦩', '🕊️', '🐇', '🦝', '🦨', '🦡', '🦦', '🦥', '🐁', '🐀', '🐿️', '🦫', '🌵', '🎄', '🌲', '🌳', '🌴', '🌱', '🌿', '☘️', '🍀', '🎍', '🎋', '🍃', '🍂', '🍁', '🍄', '🐚', '🌾', '💐', '🌷', '🌹', '🥀', '🌺', '🌸', '🌼', '🌻', '🌞', '🌝', '🌛', '🌜', '🌚', '🌕', '🌖', '🌗', '🌘', '🌑', '🌒', '🌓', '🌔', '🌙', '🌎', '🌍', '🌏', '🪐', '💫', '⭐', '🌟', '✨', '⚡', '☄️', '💥', '🔥', '🌪️', '🌈', '☀️', '🌤️', '⛅', '🌥️', '☁️', '🌦️', '🌧️', '⛈️', '🌩️', '🌨️', '❄️', '☃️', '⛄', '🌬️', '💨', '💧', '💦', '☔', '☂️', '🌊',
                        // Additional animals & nature
                        '🦫', '🦤', '🪶', '🦭', '🪲', '🪳', '🪰', '🪱', '🪴', '🫚', '🫛', '🫒', '🫑', '🫐', '🪺', '🪹', '🪸', '🪷', '🪻', '🪼', '🫎', '🫏', '🦬', '🦙', '🦒', '🦘', '🦥', '🦦', '🦨', '🦡', '🦃', '🦚', '🦜', '🦢', '🦩', '🕊️', '🐦‍⬛', '🪿', '🦤', '🪽', '🪺', '🪹', '🪸', '🪷', '🪻', '🪼']
                    },
                    {
                        name: 'food',
                        label: '🍕',
                        title: 'Food & Drink',
                        emojis: ['🍏', '🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍈', '🍒', '🍑', '🥭', '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦', '🥬', '🥒', '🌶️', '🫑', '🌽', '🥕', '🫒', '🧄', '🧅', '🥔', '🍠', '🥐', '🥯', '🍞', '🥖', '🥨', '🧀', '🥚', '🍳', '🧈', '🥞', '🧇', '🍗', '🍖', '🦴', '🥩', '🍔', '🍟', '🍕', '🌭', '🥪', '🌮', '🌯', '🫔', '🥙', '🧆', '🥘', '🍝', '🍜', '🍲', '🍛', '🍣', '🍱', '🥟', '🦪', '🍤', '🍙', '🍚', '🍘', '🍥', '🥠', '🥮', '🍢', '🍡', '🍧', '🍨', '🍦', '🥧', '🧁', '🍰', '🎂', '🍮', '🍭', '🍬', '🍫', '🍿', '🍩', '🍪', '🌰', '🥜', '🍯', '🥛', '🍼', '🫖', '☕', '🍵', '🧃', '🥤', '🧋', '🍶', '🍺', '🍻', '🥂', '🍷', '🥃', '🍸', '🍹', '🧉', '🍾', '🧊',
                        // Additional food & drink
                        '🫓', '🫔', '🥖', '🥨', '🥯', '🥞', '🧇', '🧀', '🍖', '🍗', '🥩', '🥓', '🍔', '🍟', '🍕', '🌭', '🥪', '🌮', '🌯', '🫔', '🥙', '🧆', '🥚', '🍳', '🥘', '🍲', '🫕', '🥣', '🥗', '🍿', '🧈', '🧂', '🥫', '🍱', '🍘', '🍙', '🍚', '🍛', '🍜', '🍝', '🍠', '🍢', '🍣', '🍤', '🍥', '🥮', '🍡', '🥟', '🥠', '🥡', '🦀', '🦞', '🦐', '🦑', '🦪', '🍦', '🍧', '🍨', '🍩', '🍪', '🎂', '🍰', '🧁', '🥧', '🍫', '🍬', '🍭', '🍮', '🍯', '🍼', '🥛', '☕', '🫖', '🍵', '🍶', '🍾', '🍷', '🍸', '🍹', '🍺', '🍻', '🥂', '🥃', '🥤', '🧋', '🧃', '🧉', '🧊','🥒','🍆']
                    },
                    {
                        name: 'travel',
                        label: '🚗',
                        title: 'Travel & Places',
                        emojis: ['🚗', '🚕', '🚌', '🚎', '🏎️', '🚓', '🚑', '🚒', '🚐', '🚚', '🚛', '🚜', '🛵', '🚲', '🛴', '🏍️', '🛺', '🚨', '🚔', '🚍', '🚘', '🚖', '🚡', '🚠', '🚟', '🚃', '🚋', '🚞', '🚝', '🚄', '🚅', '🚈', '🚂', '🚆', '🚇', '🚊', '🚉', '✈️', '🛫', '🛬', '🛩️', '💺', '🛰️', '🚀', '🛸', '🚁', '🛶', '⛵', '🚤', '🛥️', '⛴️', '🛳️', '🚢', '⚓', '🚧', '⛽', '🚏', '🚦', '🚥', '🗺️', '🗿', '🗽', '🗼', '🏰', '🏯', '🏟️', '🎡', '🎢', '🎠', '⛲', '⛱️', '🏖️', '🏝️', '🏜️', '🌋', '⛰️', '🏔️', '🗻', '🏕️', '🏛️', '🏗️', '🏘️', '🏠', '🏡', '🏢', '🏣', '🏤', '🏥', '🏦', '🏨', '🏩', '🏪', '🏫', '🏬', '🏭', '🏯', '🏰', '💒', '🗼', '🗽', '⛪', '🕌', '🛕', '🕍', '⛩️', '🕋',
                        // Additional travel & places
                        '🛞', '🛼', '🛶', '🛷', '🛸', '🛰️', '🛩️', '🛫', '🛬', '🛥️', '🛳️', '⛴️', '🛟', '🛝', '🛤️', '🛣️', '🛑', '🛢️', '🦴', '🎙️', '🛰️', '🛎️', '🛏️', '🛋️', '🛁', '🛀', '🛌', '🛒', '🛍️', '🛎️', '🛏️', '🛋️', '🛁', '🛀', '🛌', '🛒', '🛍️', '🛎️', '🛏️', '🛋️', '🛁', '🛀', '🛌', '🛒', '🛍️']
                    },
                    {
                        name: 'activities',
                        label: '⚽',
                        title: 'Activities',
                        emojis: ['⚽', '⚾', '🥎', '🏀', '🏐', '🏈', '🏉', '🎾', '🥏', '🎳', '🏏', '🏑', '🏒', '🥍', '🏓', '🏸', '🥊', '🥋', '🥅', '⛳', '⛸️', '🎣', '🤿', '🎽', '🎿', '🛷', '🥌', '🎯', '🪀', '🪁', '🎱', '🔮', '🧿', '🎮', '🕹️', '🎰', '🎲', '🧩', '🧸', '🪅', '🪆', '♠️', '♥️', '♦️', '♣️', '♟️', '🃏', '🀄', '🎴', '🎭', '🖼️', '🎨', '🧵', '🪡', '🧶', '🪢', '👓', '🕶️', '🥽', '🥼', '🦺', '👔', '👕', '👖', '🧣', '🧤', '🧥', '🧦', '👗', '👘', '🥻', '🩱', '🩲', '🩳', '👙', '👚', '👛', '👜', '👝', '🛍️', '🎒', '🩴', '👞', '👟', '🥾', '🥿', '👠', '👡', '🩰', '👢', '👑', '👒', '🎩', '🎓', '🧢', '🪖', '⛑️', '📿', '💄', '💍', '💎',
                        // Additional activities
                        '🛹', '🛼', '🛶', '🛷', '🛸', '🛰️', '🛩️', '🛫', '🛬', '🛥️', '🛳️', '⛴️', '🛟', '🛝', '🛤️', '🛣️', '🛑', '🛢️', '🛞', '🛟', '🛰️', '🛎️', '🛏️', '🛋️', '🛁', '🛀', '🛌', '🛒', '🛍️', '🛎️', '🛏️', '🛋️', '🛁', '🛀', '🛌', '🛒', '🛍️']
                    },
                    {
                        name: 'objects',
                        label: '💡',
                        title: 'Objects',
                        emojis: ['⌚', '📱', '📲', '💻', '⌨️', '🖥️', '🖨️', '🖱️', '🖲️', '🕹️', '🗜️', '💽', '💾', '💿', '📀', '📼', '📷', '📸', '📹', '🎥', '📽️', '🎞️', '📞', '☎️', '📟', '📠', '📺', '📻', '🎙️', '🎚️', '🎛️', '🧭', '⏱️', '⏲️', '⏰', '🕰️', '⌛', '⏳', '📡', '🔋', '🔌', '💡', '🔦', '🕯️', '🧯', '🛢️', '💸', '💵', '💴', '💶', '💷', '💰', '🪙', '💳', '💎', '✉️', '📧', '📨', '📩', '📤', '📥', '📦', '📫', '📪', '📬', '📭', '📮', '🗳️', '✏️', '✒️', '🖋️', '🖊️', '🖌️', '🖍️', '📝', '💼', '📁', '📂', '🗂️', '📅', '📆', '🗒️', '🗓️', '📇', '📈', '📉', '📊', '📋', '📌', '📍', '📎', '🖇️', '📏', '📐', '✂️', '🗃️', '🗄️', '🗑️', '🔒', '🔓', '🔏', '🔐', '🔑', '🗝️', '🔨', '🪓', '⛏️', '⚒️', '🛠️', '🗡️', '⚔️', '🔫', '🪃', '🏹', '🛡️', '🔧', '🔩', '⚙️', '🗜️', '⚖️', '🦯', '🔗', '⛓️', '🪝', '🧰', '🧲', '🪜', '⚗️', '🧪', '🧫', '🧬', '🔬', '🔭', '📡', '💉', '🩸', '💊', '🩹', '🩺', '🚪', '🛗', '🪞', '🪟', '🛏️', '🛋️', '🪑', '🚽', '🪠', '🚿', '🛁', '🪤', '🪒', '🧴', '🧷', '🧹', '🧺', '🧻', '🪣', '🧼', '🪥', '🧽', '🧯', '🛒',
                        // Additional objects
                        '🪙', '🪣', '🪤', '🪥', '🪦', '🪧', '🪑', '🪠', '🪞', '🪟', '🪔', '🪕', '🪗', '🪘', '🪙', '🪚', '🪛', '🪜', '🪝', '🪞', '🪟', '🪠', '🪡', '🪢', '🪣', '🪤', '🪥', '🪦', '🪧', '🪨', '🪰', '🪱', '🪲', '🪳', '🪴', '🪵', '🪶', '🪷', '🪸', '🪹', '🪺', '🪻', '🪼']
                    },
                    {
                        name: 'symbols',
                        label: '❤️',
                        title: 'Symbols',
                        emojis: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️', '✝️', '☪️', '🕉️', '☸️', '✡️', '🔯', '🕎', '☯️', '☦️', '🛐', '⛎', '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓', '🆔', '⚛️', '🉑', '☢️', '☣️', '📴', '📳', '🈶', '🈚', '🈸', '🈺', '🈷️', '✴️', '🆚', '💮', '🉐', '㊙️', '㊗️', '🈴', '🈵', '🈹', '🈲', '🅰️', '🅱️', '🆎', '🆑', '🅾️', '🆘', '❌', '⭕', '🛑', '⛔', '📛', '🚫', '💯', '💢', '♨️', '🚷', '🚯', '🚳', '🚱', '🔞', '📵', '🚭', '❗', '❕', '❓', '❔', '‼️', '⁉️', '🔅', '🔆', '〽️', '⚠️', '🚸', '🔱', '⚜️', '🔰', '♻️', '✅', '🈯', '💹', '❇️', '✳️', '❎', '🌐', '💠', 'Ⓜ️', '🌀', '💤', '🏧', '🚾', '♿', '🅿️', '🈳', '🈂️', '🛂', '🛃', '🛄', '🛅', '🚹', '🚺', '🚼', '🚻', '🚮', '🎦', '📶', '🈁', '🔣', 'ℹ️', '🔤', '🔡', '🔠', '🆖', '🆗', '🆙', '🆒', '🆕', '🆓', '0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '🔢', '#️⃣', '*️⃣', '⏏️', '▶️', '⏸', '⏯', '⏹', '⏺', '⏭', '⏮', '⏩', '⏪', '⏫', '⏬', '◀️', '🔼', '🔽', '➡️', '⬅️', '⬆️', '⬇️', '↗️', '↘️', '↙️', '↖️', '↕️', '↔️', '↪️', '↩️', '⤴️', '⤵️', '🔀', '🔁', '🔂', '🔄', '🔃', '🎵', '🎶', '➕', '➖', '➗', '✖️', '♾', '💲', '💱', '™️', '©️', '®️', '〰️', '➰', '➿', '🔚', '🔙', '🔛', '🔝', '🔜',
                        // Additional symbols
                        '🫰', '🫱', '🫲', '🫳', '🫴', '🫵', '🫶', '🫦', '🫅', '🫃', '🫄', '🫷', '🫸', '🫺', '🫰', '🫱', '🫲', '🫳', '🫴', '🫵', '🫶', '🫦', '🫅', '🫃', '🫄', '🫷', '🫸', '🫺']
                    }
                ];

                let currentCategory = emojiCategories[0];

                // Create tabs
                emojiCategories.forEach((category, index) => {
                    const tab = document.createElement('button');
                    tab.className = 'emoji-tab';
                    tab.textContent = category.label;
                    tab.title = category.title;
                    tab.style.background = 'none';
                    tab.style.border = 'none';
                    tab.style.padding = '8px';
                    tab.style.cursor = 'pointer';
                    tab.style.borderRadius = '6px';
                    tab.style.fontSize = '18px';
                    tab.style.transition = 'background-color 0.2s';

                    if (index === 0) {
                        tab.style.backgroundColor = '#f0f0f0';
                    }

                    tab.addEventListener('mouseover', () => {
                        tab.style.backgroundColor = '#f5f5f5';
                    });

                    tab.addEventListener('mouseout', () => {
                        if (category !== currentCategory) {
                            tab.style.backgroundColor = 'transparent';
                        }
                    });

                    tab.addEventListener('click', () => {
                        // Update active tab
                        tabsContainer.querySelectorAll('.emoji-tab').forEach(t => {
                            t.style.backgroundColor = 'transparent';
                        });
                        tab.style.backgroundColor = '#f0f0f0';

                        // Show selected category
                        currentCategory = category;
                        renderEmojis(category.emojis);
                    });

                    tabsContainer.appendChild(tab);
                });

                // Function to render emojis
                function renderEmojis(emojis) {
                    emojiContent.innerHTML = '';

                    emojis.filter(emoji => emoji !== '🏳️‍🌈').forEach(emoji => {
                        const emojiSpan = document.createElement('span');
                        emojiSpan.className = 'emoji-item';
                        emojiSpan.textContent = emoji;
                        emojiSpan.style.cursor = 'pointer';
                        emojiSpan.style.fontSize = '22px';
                        emojiSpan.style.textAlign = 'center';
                        emojiSpan.style.padding = '5px';
                        emojiSpan.style.borderRadius = '6px';
                        emojiSpan.style.transition = 'all 0.2s ease';

                        emojiSpan.addEventListener('mouseover', () => {
                            emojiSpan.style.backgroundColor = '#f0f0f0';
                            emojiSpan.style.transform = 'scale(1.1)';
                        });

                        emojiSpan.addEventListener('mouseout', () => {
                            emojiSpan.style.backgroundColor = 'transparent';
                            emojiSpan.style.transform = 'scale(1)';
                        });

                        emojiSpan.addEventListener('click', () => {
                            messageInput.value += emoji;
                            adjustTextareaHeight();
                            // DON'T close the panel - let user keep selecting emojis!
                            emojiSpan.style.backgroundColor = '#d4edda';
                            setTimeout(() => {
                                emojiSpan.style.backgroundColor = 'transparent';
                            }, 300);
                        });

                        emojiContent.appendChild(emojiSpan);
                    });
                }

                // Render initial category
                renderEmojis(currentCategory.emojis);

                // Add elements to panel
                customEmojiPanel.appendChild(panelHeader);
                customEmojiPanel.appendChild(tabsContainer);
                customEmojiPanel.appendChild(emojiContent);

                document.body.appendChild(customEmojiPanel);
                return customEmojiPanel;
            }

            // Create the custom emoji panel
            const customEmojiPanel = createCustomEmojiPanel();

            // Modify the emoji button click handler - toggle panel visibility
            emojiBtn.addEventListener('click', () => {
                const isVisible = customEmojiPanel.style.display === 'flex';

                if (isVisible) {
                    customEmojiPanel.style.display = 'none';
                } else {
                    const rect = emojiBtn.getBoundingClientRect();
                    customEmojiPanel.style.display = 'flex';
                    customEmojiPanel.style.bottom = `${window.innerHeight - rect.top + 10}px`;
                    customEmojiPanel.style.left = '20px';

                    // Focus on the panel for better accessibility
                    customEmojiPanel.focus();
                }
            });

            // Close emoji panel only when clicking outside (not on emojis or tabs)
            document.addEventListener('click', (e) => {
                const isEmojiBtn = emojiBtn.contains(e.target);
                const isEmojiPanel = customEmojiPanel.contains(e.target);
                const isEmojiItem = e.target.classList.contains('emoji-item');
                const isEmojiTab = e.target.classList.contains('emoji-tab');

                if (!isEmojiBtn && !isEmojiPanel && customEmojiPanel.style.display === 'flex') {
                    customEmojiPanel.style.display = 'none';
                }
            });

            // Also add the original emoji picker functionality as fallback
            if (emojiPicker) {
                emojiPicker.addEventListener('emoji-click', event => {
                    if (event.detail.unicode !== '🏳️‍🌈') {
                        messageInput.value += event.detail.unicode;
                        adjustTextareaHeight();
                        emojiPickerContainer.classList.remove('visible');
                    }
                });
            }

            // Add keyboard support for better accessibility
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && customEmojiPanel.style.display === 'flex') {
                    customEmojiPanel.style.display = 'none';
                }
            });

            // Check if user is already logged in via session
            checkSession();
        });

        function initSocketConnection() {
            // In a real app, you would connect to your WebSocket server here
            // For this demo, we'll simulate real-time updates with setTimeout
            console.log("Simulating WebSocket connection...");

            // Simulate receiving real-time updates
            setInterval(() => {
                if (currentUser) {
                    // Simulate new messages or status updates
                    if (Math.random() > 0.8 && chats.length > 0) {
                        const randomChat = chats[Math.floor(Math.random() * chats.length)];
                        if (randomChat.userId !== currentUser.id) {
                            simulateReply(randomChat.userId);
                        }
                    }

                    // Simulate status updates from contacts
                    if (Math.random() > 0.9 && users.length > 0) {
                        const randomUser = users[Math.floor(Math.random() * users.length)];
                        if (randomUser.id !== currentUser.id && !blockedUsers.includes(randomUser.id)) {
                            simulateStatusUpdate(randomUser.id);
                        }
                    }
                }
            }, 10000); // Check every 10 seconds
        }

        async function checkSession() {
            try {
                const response = await fetch('/api/session');
                const data = await response.json();
                if (data.user) {
                    currentUser = data.user;
                    users = data.users || [];
                    showApp();
                } else {
                    showAuth();
                }
            } catch (error) {
                console.error('Session check failed:', error);
                showAuth();
            }
        }

        function loadData() {
            // Load from server via API
            fetchUserData();
        }

        async function fetchUserData() {
            try {
                const response = await fetch('/api/user/data');
                const data = await response.json();
                users = data.users || [];
                chats = data.chats || [];
                groups = data.groups || [];
                statusUpdates = data.statusUpdates || [];
                blockedUsers = data.blockedUsers || [];
            } catch (error) {
                console.error('Failed to load user data:', error);
            }
        }

        function generateSampleChats() {
            if (!currentUser || users.length === 0) return [];

            // Create chats with the first 3 users (for demo purposes)
            return [
                {
                    id: '1',
                    userId: users[0]?.id || '1',
                    messages: [
                        {
                            id: '1-1',
                            sender: users[0]?.id || '1',
                            content: 'Hey, how are you doing?',
                            timestamp: new Date(Date.now() - 86400000).toISOString(),
                            status: 'read'
                        },
                        {
                            id: '1-2',
                            sender: currentUser?.id || '2',
                            content: 'I\\'m good, thanks! How about you?',
                            timestamp: new Date(Date.now() - 82800000).toISOString(),
                            status: 'read'
                        },
                        {
                            id: '1-3',
                            sender: users[0]?.id || '1',
                            content: 'Doing well! Just wanted to check in.',
                            timestamp: new Date(Date.now() - 79200000).toISOString(),
                            status: 'read'
                        },
                        {
                            id: '1-4',
                            sender: users[0]?.id || '1',
                            type: 'image',
                            content: {
                                url: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb',
                                caption: 'Beautiful landscape from my trip'
                            },
                            timestamp: new Date(Date.now() - 72000000).toISOString(),
                            status: 'read'
                        }
                    ],
                    unreadCount: 0
                },
                {
                    id: '2',
                    userId: users[1]?.id || '2',
                    messages: [
                        {
                            id: '2-1',
                            sender: users[1]?.id || '2',
                            content: 'Can we meet tomorrow?',
                            timestamp: new Date(Date.now() - 3600000).toISOString(),
                            status: 'delivered'
                        },
                        {
                            id: '2-2',
                            sender: currentUser?.id || '2',
                            content: 'Sure, what time works for you?',
                            timestamp: new Date(Date.now() - 1800000).toISOString(),
                            status: 'read'
                        }
                    ],
                    unreadCount: 1
                }
            ];
        }

        function generateSampleGroups() {
            if (!currentUser || users.length === 0) return [];

            return [
                {
                    id: 'g1',
                    name: 'Family Group',
                    avatar: 'https://cdn-icons-png.flaticon.com/512/3132/3132779.png',
                    members: [
                        { userId: currentUser.id, isAdmin: true },
                        { userId: users[0]?.id || '1', isAdmin: false },
                        { userId: users[1]?.id || '2', isAdmin: false }
                    ],
                    messages: [
                        {
                            id: 'g1-1',
                            sender: users[0]?.id || '1',
                            content: 'Hey everyone! How are you doing?',
                            timestamp: new Date(Date.now() - 86400000).toISOString()
                        },
                        {
                            id: 'g1-2',
                            sender: currentUser.id,
                            content: 'Doing great! How about you?',
                            timestamp: new Date(Date.now() - 82800000).toISOString()
                        }
                    ],
                    unreadCount: 0
                }
            ];
        }

        function generateSampleStatusUpdates() {
            if (users.length === 0) return [];

            return [
                {
                    id: '1',
                    userId: users[0]?.id || '1',
                    media: {
                        type: 'image',
                        url: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb'
                    },
                    caption: 'Beautiful landscape from my trip',
                    timestamp: new Date(Date.now() - 3600000).toISOString(),
                    views: 12,
                    likes: ['user2', 'user3'],
                    comments: [
                        {
                            userId: 'user2',
                            text: 'Amazing view!',
                            timestamp: new Date(Date.now() - 3500000).toISOString()
                        },
                        {
                            userId: 'user3',
                            text: 'Where is this?',
                            timestamp: new Date(Date.now() - 3400000).toISOString()
                        }
                    ]
                },
                {
                    id: '2',
                    userId: users[1]?.id || '2',
                    media: {
                        type: 'video',
                        url: 'https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4'
                    },
                    caption: 'Check out this cool video!',
                    timestamp: new Date(Date.now() - 7200000).toISOString(),
                    views: 24,
                    likes: ['user1', 'user3'],
                    comments: [
                        {
                            userId: 'user1',
                            text: 'Nice video!',
                            timestamp: new Date(Date.now() - 7100000).toISOString()
                        }
                    ]
                }
            ];
        }

        function initEventListeners() {
            // Auth event listeners
            loginForm.addEventListener('submit', handleLogin);
            registerForm.addEventListener('submit', handleRegister);
            switchToRegister.addEventListener('click', (e) => {
                e.preventDefault();
                loginForm.classList.remove('active');
                registerForm.classList.add('active');
            });
            switchToLogin.addEventListener('click', (e) => {
                e.preventDefault();
                registerForm.classList.remove('active');
                loginForm.classList.add('active');
            });
            uploadAvatarBtn.addEventListener('click', () => registerAvatar.click());
            registerAvatar.addEventListener('change', handleAvatarUpload);

            // Chat event listeners
            newChatBtn.addEventListener('click', showNewChatModal);
            newGroupBtn.addEventListener('click', showNewGroupModal);
            attachBtn.addEventListener('click', () => fileInput.click());
            sendBtn.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            messageInput.addEventListener('input', adjustTextareaHeight);
            messageInput.addEventListener('input', handleTyping);
            emojiBtn.addEventListener('click', toggleEmojiPicker);
            voiceMessageBtn.addEventListener('click', startVoiceRecording);
            fileInput.addEventListener('change', handleFileUpload);

            // Search users
            searchUsersInput.addEventListener('input', filterUsersAndChats);
            searchContactsInput.addEventListener('input', filterContacts);

            // Status click handler
            currentUserStatus.addEventListener('click', () => {
                if (currentUser) {
                    showUserPosts(currentUser);
                }
            });

            // Modal event listeners
            closeModals.forEach(btn => {
                btn.addEventListener('click', closeAllModals);
            });

            // Status view event listeners
            statusBtn.addEventListener('click', showStatusView);
            backToChatsBtn.addEventListener('click', hideStatusView);
            backToChatsBtnMobile.addEventListener('click', () => {
                document.getElementById('sidebar').classList.remove('hidden');
                chatArea.classList.remove('active');
            });
            addStatusBtn.addEventListener('click', showCreateStatusModal);
            selectStatusMediaBtn.addEventListener('click', () => statusMediaInput.click());
            statusMediaInput.addEventListener('change', handleStatusMediaUpload);
            postStatusBtn.addEventListener('click', postStatusUpdate);

            // User menu event listeners
            userMenuBtn.addEventListener('click', toggleUserMenu);
            profileBtn.addEventListener('click', showProfileModal);
            logoutBtn.addEventListener('click', logout);
            toggleDarkModeBtn.addEventListener('click', toggleDarkMode);

            // Profile modal event listeners
            profileAvatarEdit.addEventListener('click', () => profileAvatarInput.click());
            profileAvatarInput.addEventListener('change', handleProfileAvatarUpload);
            cancelProfileBtn.addEventListener('click', closeAllModals);
            saveProfileBtn.addEventListener('click', saveProfile);

            // Chat menu event listeners
            chatMenuBtn.addEventListener('click', toggleChatMenu);
            blockUserBtn.addEventListener('click', blockCurrentUser);
            deleteChatBtn.addEventListener('click', deleteCurrentChat);
            manageGroupBtn.addEventListener('click', manageCurrentGroup);

            // Video call event listeners
            voiceCallBtn.addEventListener('click', startVoiceCall);
            videoCallBtn.addEventListener('click', startVideoCall);
            muteCallBtn.addEventListener('click', toggleMute);
            endCallBtn.addEventListener('click', endCall);
            videoToggleBtn.addEventListener('click', toggleVideo);

            // Post navigation event listeners
            postPrev.addEventListener('click', () => scrollToPost(currentPostIndex - 1));
            postNext.addEventListener('click', () => scrollToPost(currentPostIndex + 1));

            // Post interaction event listeners
            likePostBtn.addEventListener('click', toggleLikePost);
            commentPostBtn.addEventListener('click', toggleComments);
            closeCommentsBtn.addEventListener('click', toggleComments);
            submitCommentBtn.addEventListener('click', addCommentToPost);
            commentInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    addCommentToPost();
                }
            });
            commentInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });

            // Group creation event listeners
            groupAvatar.addEventListener('click', () => groupAvatarInput.click());
            groupAvatarInput.addEventListener('change', handleGroupAvatarUpload);
            createGroupBtn.addEventListener('click', createGroup);

            // Group management event listeners
            cancelGroupManagementBtn.addEventListener('click', closeAllModals);
            saveGroupChangesBtn.addEventListener('click', saveGroupChanges);
            groupPhotoInput.addEventListener('change', handleGroupPhotoChange);

            // Touch events for status posts
            postsContainer.addEventListener('touchstart', (e) => {
                touchStartX = e.changedTouches[0].screenX;
            }, false);

            postsContainer.addEventListener('touchend', (e) => {
                touchEndX = e.changedTouches[0].screenX;
                handleSwipe();
            }, false);

            // Click outside modals to close them
            window.addEventListener('click', (e) => {
                if (e.target.classList.contains('modal')) {
                    closeAllModals();
                }

                // Close user menu when clicking outside
                if (!userMenuBtn.contains(e.target) && !userMenuModal.contains(e.target)) {
                    userMenuModal.style.display = 'none';
                }

                // Close chat menu when clicking outside
                if (!chatMenuBtn.contains(e.target) && !chatMenuModal.contains(e.target)) {
                    chatMenuModal.style.display = 'none';
                }

                // Close emoji picker when clicking outside
                if (!emojiBtn.contains(e.target) && !emojiPickerContainer.contains(e.target)) {
                    emojiPickerContainer.classList.remove('visible');
                }
            });
        }

        function handleSwipe() {
            const threshold = 50; // Minimum distance to consider it a swipe
            const diff = touchEndX - touchStartX;

            if (Math.abs(diff) > threshold) {
                if (diff > 0) {
                    // Swipe right - previous post
                    scrollToPost(currentPostIndex - 1);
                } else {
                    // Swipe left - next post
                    scrollToPost(currentPostIndex + 1);
                }
            }
        }

        function adjustTextareaHeight() {
            messageInput.style.height = 'auto';
            messageInput.style.height = (messageInput.scrollHeight) + 'px';
        }

        function handleTyping() {
            // In a real app, you would send a typing indicator to the other user
            if (currentChat) {
                console.log(`${currentUser.name} is typing...`);
                // Clear previous timeout
                if (typingTimeout) clearTimeout(typingTimeout);

                // Set new timeout
                typingTimeout = setTimeout(() => {
                    console.log(`${currentUser.name} stopped typing`);
                }, 2000);
            }
        }

        function toggleEmojiPicker() {
            emojiPickerContainer.classList.toggle('visible');
        }

        function startVoiceRecording() {
            alert("Voice recording functionality would be implemented here");
            // In a real app, you would use the Web Audio API to record voice
        }

        function handleFileUpload(e) {
            const file = e.target.files[0];
            if (!file) return;


            // Check file size (max 10MB)
            if (file.size < 100 * 1024 * 1024) {
                alert("File size should be less than 10MB");
                return;
            }

            // Determine file type
            const fileType = file.type.split('/')[0];
            const isImage = fileType === 'image';
            const isVideo = fileType === 'video';
            const isAudio = fileType === 'audio';
            const isDocument = !isImage && !isVideo && !isAudio;

            // Create a preview of the file
            const reader = new FileReader();
            reader.onload = function(e) {
                if (isImage) {
                    // For images, show preview and send as image message
                    sendMessage({
                        type: 'image',
                        content: {
                            url: e.target.result,
                            caption: ''
                        }
                    });
                } else if (isVideo) {
                    // For videos, send as video message
                    sendMessage({
                        type: 'video',
                        content: {
                            url: e.target.result,
                            caption: ''
                        }
                    });
                } else if (isAudio) {
                    // For audio, send as audio message
                    sendMessage({
                        type: 'audio',
                        content: {
                            url: e.target.result,
                            caption: ''
                        }
                    });
                } else {
                    // For documents, send as document message
                    sendMessage({
                        type: 'document',
                        content: {
                            url: e.target.result,
                            filename: file.name,
                            size: formatFileSize(file.size)
                        }
                    });
                }
            };

            if (isImage || isVideo || isAudio) {
                reader.readAsDataURL(file);
            } else {
                // For documents, we don't need to preview
                sendMessage({
                    type: 'document',
                    content: {
                        url: '#',
                        filename: file.name,
                        size: formatFileSize(file.size)
                    }
                });
            }

            // Reset file input
            fileInput.value = '';
        }

        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB','TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        function sendMessage(messageContent = null) {
            if (!currentChat || (!messageInput.value && !messageContent)) return;

            let message;
            if (messageContent) {
                // If message content is provided (for files, etc.)
                message = {
                    id: generateId(),
                    ...messageContent,
                    sender: currentUser.id,
                    timestamp: new Date().toISOString(),
                    status: 'sent'
                };
            } else {
                // Regular text message
                message = {
                    id: generateId(),
                    sender: currentUser.id,
                    content: messageInput.value,
                    timestamp: new Date().toISOString(),
                    status: 'sent'
                };
                messageInput.value = '';
                adjustTextareaHeight();
            }

            // Add message to current chat
            const chat = chats.find(c => c.id === currentChat.id);
            if (chat) {
                if (!chat.messages) chat.messages = [];
                chat.messages.push(message);
                saveChats();
                renderMessages(chat.messages);

                // Scroll to bottom
                messagesContainer.scrollTop = messagesContainer.scrollHeight;

                // Simulate reply after 1-3 seconds
                if (Math.random() > 0.5) {
                    setTimeout(() => simulateReply(chat.userId || chat.id), 1000 + Math.random() * 2000);
                }
            }
        }

        function simulateReply(userId) {
            const user = users.find(u => u.id === userId);
            if (!user || blockedUsers.includes(user.id)) return;

            const chat = chats.find(c => c.userId === userId || (c.members && c.members.some(m => m.userId === userId)));
            if (!chat) return;

            const replies = [
                "Hey, how are you?",
                "What's up?",
                "I'll call you later",
                "Thanks for the message!",
                "Can we talk tomorrow?",
                "I'm busy right now",
                "Let's meet soon",
                "Did you see my last message?",
                "I'll get back to you",
                "Sounds good!"
            ];

            const randomReply = replies[Math.floor(Math.random() * replies.length)];

            const message = {
                id: generateId(),
                sender: user.id,
                content: randomReply,
                timestamp: new Date().toISOString(),
                status: 'delivered'
            };

            if (!chat.messages) chat.messages = [];
            chat.messages.push(message);
            saveChats();

            // Update UI if this is the current chat
            if (currentChat && currentChat.id === chat.id) {
                renderMessages(chat.messages);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            } else {
                // Update chat list to show new message
                renderChats();
            }
        }

        function simulateStatusUpdate(userId) {
            const user = users.find(u => u.id === userId);
            if (!user || blockedUsers.includes(user.id)) return;

            const statusOptions = [
                {
                    type: 'image',
                    url: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb',
                    caption: 'Beautiful day outside!'
                },
                {
                    type: 'image',
                    url: 'https://images.unsplash.com/photo-1519125323398-675f0ddb6308',
                    caption: 'Enjoying my vacation'
                },
                {
                    type: 'video',
                    url: 'https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4',
                    caption: 'Check this out!'
                }
            ];

            const randomStatus = statusOptions[Math.floor(Math.random() * statusOptions.length)];

            const statusUpdate = {
                id: generateId(),
                userId: user.id,
                media: {
                    type: randomStatus.type,
                    url: randomStatus.url
                },
                caption: randomStatus.caption,
                timestamp: new Date().toISOString(),
                views: 0,
                likes: [],
                comments: []
            };

            statusUpdates.push(statusUpdate);
            saveStatusUpdates();

            // Update status view if open
            if (statusView.style.display === 'flex') {
                renderStatusList();
            }
        }

        function generateId() {
            return Math.random().toString(36).substr(2, 9);
        }

        async function handleLogin(e) {
            e.preventDefault();
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();

                if (response.ok) {
                    currentUser = data.user;
                    users = data.users || [];
                    showApp();
                } else {
                    alert(data.error || 'Invalid email or password');
                }
            } catch (error) {
                console.error('Login failed:', error);
                alert('Login failed. Please try again.');
            }
        }

        async function handleRegister(e) {
            e.preventDefault();
            const name = document.getElementById('register-name').value;
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const avatar = avatarPreview.querySelector('img')?.src || '';

            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ name, email, password, avatar })
                });

                const data = await response.json();

                if (response.ok) {
                    currentUser = data.user;
                    users = data.users || [];
                    showApp();
                } else {
                    alert(data.error || 'Registration failed');
                }
            } catch (error) {
                console.error('Registration failed:', error);
                alert('Registration failed. Please try again.');
            }
        }

        function handleAvatarUpload(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                // Create img element if it doesn't exist
                let img = avatarPreview.querySelector('img');
                if (!img) {
                    img = document.createElement('img');
                    avatarPreview.innerHTML = '';
                    avatarPreview.appendChild(img);
                }
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }

        function showApp() {
            authContainer.style.display = 'none';
            appContainer.style.display = 'flex';

            // Render UI
            renderCurrentUser();
            renderContacts();
            renderChats();

            // Set dark mode if enabled
            if (localStorage.getItem('darkMode') === 'true') {
                toggleDarkMode();
            }
        }

        function showAuth() {
            authContainer.style.display = 'flex';
            appContainer.style.display = 'none';
            loginForm.classList.add('active');
            registerForm.classList.remove('active');
        }

        function renderCurrentUser() {
            if (!currentUser) return;

            currentUserName.textContent = currentUser.name;
            if (currentUser.avatar) {
                currentUserAvatar.src = currentUser.avatar;
                currentUserAvatar.style.display = 'block';
            } else {
                currentUserAvatar.style.display = 'none';
            }

            // Also update profile modal if open
            if (profileModal.style.display === 'flex') {
                renderProfileModal();
            }
        }

        function renderContacts() {
            usersList.innerHTML = '';

            // Filter out current user and blocked users
            const filteredContacts = users.filter(user =>
                user.id !== currentUser.id && !blockedUsers.includes(user.id)
            );

            if (filteredContacts.length === 0) {
                usersList.innerHTML = '<div class="empty-content"><p>No contacts found</p></div>';
                return;
            }

            filteredContacts.forEach(user => {
                const userItem = document.createElement('div');
                userItem.className = 'user-item';
                userItem.innerHTML = `
                    <div class="avatar">
                        ${user.avatar ? `<img src="${user.avatar}" alt="${user.name}">` : `<i class="fas fa-user"></i>`}
                    </div>
                    <div class="user-info">
                        <div class="user-info-header">
                            <span class="user-name">${user.name}</span>
                        </div>
                        <span class="user-status ${user.lastSeen > new Date(Date.now() - 300000).toISOString() ? 'online' : ''}">
                            ${user.lastSeen > new Date(Date.now() - 300000).toISOString() ? 'Online' : 'Last seen recently'}
                        </span>
                    </div>
                `;
                userItem.addEventListener('click', () => startChat(user));
                usersList.appendChild(userItem);
            });
        }

        function renderChats() {
            chatsList.innerHTML = '';

            if (chats.length === 0) {
                chatsList.innerHTML = '<div class="empty-content"><p>No chats yet</p></div>';
                return;
            }

            // Sort chats by last message timestamp
            const sortedChats = [...chats].sort((a, b) => {
                const aLastMsg = a.messages?.[a.messages.length - 1]?.timestamp || '';
                const bLastMsg = b.messages?.[b.messages.length - 1]?.timestamp || '';
                return new Date(bLastMsg) - new Date(aLastMsg);
            });

            sortedChats.forEach(chat => {
                // Get the other user (for individual chats) or group info
                let chatName, chatAvatar, lastMessage, isGroup = false;

                if (chat.userId) {
                    // Individual chat
                    const user = users.find(u => u.id === chat.userId);
                    if (!user || blockedUsers.includes(user.id)) return;

                    chatName = user.name;
                    chatAvatar = user.avatar;
                } else if (chat.members) {
                    // Group chat
                    isGroup = true;
                    chatName = chat.name;
                    chatAvatar = chat.avatar;
                }

                // Get last message
                if (chat.messages && chat.messages.length > 0) {
                    const lastMsg = chat.messages[chat.messages.length - 1];
                    let previewText = '';

                    if (lastMsg.type === 'image') {
                        previewText = '📷 Photo';
                    } else if (lastMsg.type === 'video') {
                        previewText = '🎥 Video';
                    } else if (lastMsg.type === 'audio') {
                        previewText = '🎤 Audio';
                    } else if (lastMsg.type === 'document') {
                        previewText = '📄 Document';
                    } else {
                        previewText = lastMsg.content;
                    }

                    // Show sender name for group chats
                    if (isGroup && lastMsg.sender !== currentUser.id) {
                        const sender = users.find(u => u.id === lastMsg.sender);
                        if (sender) {
                            previewText = `${sender.name}: ${previewText}`;
                        }
                    }

                    lastMessage = {
                        text: previewText,
                        time: formatTime(lastMsg.timestamp),
                        isCurrentUser: lastMsg.sender === currentUser.id
                    };
                }

                const chatItem = document.createElement('div');
                chatItem.className = `chat-item ${currentChat?.id === chat.id ? 'active' : ''} ${chat.unreadCount > 0 ? 'unread' : ''}`;
                chatItem.innerHTML = `
                    <div class="avatar">
                        ${chatAvatar ? `<img src="${chatAvatar}" alt="${chatName}">` : `<i class="fas ${isGroup ? 'fa-users' : 'fa-user'}"></i>`}
                    </div>
                    <div class="chat-info">
                        <div class="chat-info-header">
                            <span class="chat-name">${chatName}</span>
                            ${lastMessage ? `<span class="chat-time">${lastMessage.time}</span>` : ''}
                        </div>
                        ${lastMessage ? `
                        <div class="chat-preview">
                            ${lastMessage.isCurrentUser ? '<i class="fas fa-check-double"></i>' : ''}
                            <span>${lastMessage.text}</span>
                            ${chat.unreadCount > 0 ? `<span class="unread-count">${chat.unreadCount}</span>` : ''}
                        </div>
                        ` : ''}
                    </div>
                `;
                chatItem.addEventListener('click', () => openChat(chat));
                chatsList.appendChild(chatItem);
            });
        }

        function formatTime(timestamp) {
            if (!timestamp) return '';

            const date = new Date(timestamp);
            const now = new Date();
            const diffInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

            if (diffInDays === 0) {
                // Today - show time
                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            } else if (diffInDays === 1) {
                // Yesterday
                return 'Yesterday';
            } else if (diffInDays < 7) {
                // Within a week - show day name
                return date.toLocaleDateString([], { weekday: 'short' });
            } else {
                // Older - show date
                return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
            }
        }

        function openChat(chat) {
            currentChat = chat;

            // Mark messages as read
            if (chat.unreadCount > 0) {
                chat.unreadCount = 0;
                saveChats();
                renderChats();
            }

            // Update UI
            if (chat.userId) {
                // Individual chat
                const user = users.find(u => u.id === chat.userId);
                if (user) {
                    document.getElementById('chat-contact-name').textContent = user.name;
                    document.getElementById('chat-contact-status').innerHTML = `
                        <span class="status-dot ${user.lastSeen > new Date(Date.now() - 300000).toISOString() ? 'online' : ''}"></span>
                        ${user.lastSeen > new Date(Date.now() - 300000).toISOString() ? 'Online' : 'Last seen recently'}
                    `;

                    const avatar = document.getElementById('chat-contact-avatar');
                    if (user.avatar) {
                        avatar.innerHTML = `<img src="${user.avatar}" alt="${user.name}">`;
                    } else {
                        avatar.innerHTML = '<i class="fas fa-user"></i>';
                    }
                }
            } else {
                // Group chat
                document.getElementById('chat-contact-name').textContent = chat.name;
                document.getElementById('chat-contact-status').innerHTML = `
                    <span>${chat.members.length} members</span>
                `;

                const avatar = document.getElementById('chat-contact-avatar');
                if (chat.avatar) {
                    avatar.innerHTML = `<img src="${chat.avatar}" alt="${chat.name}">`;
                } else {
                    avatar.innerHTML = '<i class="fas fa-users"></i>';
                }

                // Show group management button if user is admin
                const isAdmin = chat.members.some(m => m.userId === currentUser.id && m.isAdmin);
                manageGroupBtn.style.display = isAdmin ? 'block' : 'none';
            }

            // Show chat UI
            emptyChat.style.display = 'none';
            chatHeader.style.display = 'flex';
            messagesContainer.style.display = 'flex';
            messageInputContainer.style.display = 'flex';

            // Render messages
            renderMessages(chat.messages || []);

            // Scroll to bottom
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 100);

            // On mobile, hide sidebar and show chat area
            if (window.innerWidth <= 768) {
                document.getElementById('sidebar').classList.add('hidden');
                chatArea.classList.add('active');
            }
        }

        function renderMessages(messages) {
            messagesContainer.innerHTML = '';

            if (!messages || messages.length === 0) {
                messagesContainer.innerHTML = '<div class="empty-content"><p>No messages yet</p></div>';
                return;
            }

            messages.forEach(msg => {
                const isOutgoing = msg.sender === currentUser.id;
                const messageTime = formatTime(msg.timestamp);
                let messageContent = '';

                if (msg.type === 'image') {
                    messageContent = `
                        <div>${msg.content.caption || ''}</div>
                        <img src="${msg.content.url}" alt="Image" onclick="showImagePreview('${msg.content.url}')">
                    `;
                } else if (msg.type === 'video') {
                    messageContent = `
                        <div>${msg.content.caption || ''}</div>
                        <video controls>
                            <source src="${msg.content.url}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    `;
                } else if (msg.type === 'audio') {
                    messageContent = `
                        <div>${msg.content.caption || ''}</div>
                        <audio controls>
                            <source src="${msg.content.url}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                    `;
                } else if (msg.type === 'document') {
                    messageContent = `
                        <div class="message-doc">
                            <i class="fas fa-file-alt"></i>
                            <div class="doc-info">
                                <div class="doc-name">${msg.content.filename}</div>
                                <div class="doc-size">${msg.content.size}</div>
                            </div>
                        </div>
                    `;
                } else {
                    messageContent = msg.content;
                }

                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isOutgoing ? 'outgoing' : 'incoming'}`;
                messageDiv.innerHTML = `
                    ${messageContent}
                    <div class="message-time">
                        ${messageTime}
                        ${isOutgoing ? `<i class="message-status fas fa-${msg.status === 'read' ? 'check-double' : 'check'}"></i>` : ''}
                    </div>
                `;
                messagesContainer.appendChild(messageDiv);
            });
        }

        function showImagePreview(imageUrl) {
            imagePreviewImg.src = imageUrl;
            imagePreviewModal.style.display = 'flex';
        }

        function startChat(user) {
            // Check if chat already exists
            let chat = chats.find(c => c.userId === user.id);

            if (!chat) {
                // Create new chat
                chat = {
                    id: generateId(),
                    userId: user.id,
                    messages: [],
                    unreadCount: 0
                };
                chats.push(chat);
                saveChats();
            }

            // Open chat
            openChat(chat);
            closeAllModals();
        }

        function filterUsersAndChats() {
            const searchTerm = searchUsersInput.value.toLowerCase();

            if (searchTerm === '') {
                usersList.style.display = 'none';
                chatsList.style.display = 'block';
                return;
            }

            // Show users list and filter
            usersList.style.display = 'block';
            chatsList.style.display = 'none';

            const userItems = usersList.querySelectorAll('.user-item');
            userItems.forEach(item => {
                const userName = item.querySelector('.user-name').textContent.toLowerCase();
                if (userName.includes(searchTerm)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        }

        function filterContacts() {
            const searchTerm = searchContactsInput.value.toLowerCase();
            const contactItems = contactsList.querySelectorAll('.contact-item');

            contactItems.forEach(item => {
                const contactName = item.querySelector('.contact-name').textContent.toLowerCase();
                if (contactName.includes(searchTerm)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        }

        function showNewChatModal() {
            newChatModal.style.display = 'flex';
            searchContactsInput.value = '';
            filterContacts();

            // Render contacts
            contactsList.innerHTML = '';

            // Filter out current user and blocked users
            const filteredContacts = users.filter(user =>
                user.id !== currentUser.id && !blockedUsers.includes(user.id)
            );

            if (filteredContacts.length === 0) {
                contactsList.innerHTML = '<div class="empty-content"><p>No contacts found</p></div>';
                return;
            }

            filteredContacts.forEach(user => {
                const contactItem = document.createElement('div');
                contactItem.className = 'contact-item';
                contactItem.innerHTML = `
                    <div class="avatar">
                        ${user.avatar ? `<img src="${user.avatar}" alt="${user.name}">` : `<i class="fas fa-user"></i>`}
                    </div>
                    <div class="user-info">
                        <div class="user-info-header">
                            <span class="contact-name">${user.name}</span>
                        </div>
                        <span class="contact-status ${user.lastSeen > new Date(Date.now() - 300000).toISOString() ? 'online' : ''}">
                            ${user.lastSeen > new Date(Date.now() - 300000).toISOString() ? 'Online' : 'Last seen recently'}
                        </span>
                    </div>
                `;
                contactItem.addEventListener('click', () => {
                    startChat(user);
                    closeAllModals();
                });
                contactsList.appendChild(contactItem);
            });
        }

        function showNewGroupModal() {
            newGroupModal.style.display = 'flex';
            selectedGroupMembers = [];

            // Render group members list
            groupMembersList.innerHTML = '';

            // Filter out current user and blocked users
            const filteredContacts = users.filter(user =>
                user.id !== currentUser.id && !blockedUsers.includes(user.id)
            );

            if (filteredContacts.length === 0) {
                groupMembersList.innerHTML = '<div class="empty-content"><p>No contacts found</p></div>';
                return;
            }

            filteredContacts.forEach(user => {
                const memberItem = document.createElement('div');
                memberItem.className = 'group-member-item';
                memberItem.innerHTML = `
                    <input type="checkbox" class="group-member-checkbox" id="member-${user.id}" value="${user.id}">
                    <div class="avatar avatar-sm">
                        ${user.avatar ? `<img src="${user.avatar}" alt="${user.name}">` : `<i class="fas fa-user"></i>`}
                    </div>
                    <div class="user-info">
                        <div class="user-info-header">
                            <span class="contact-name">${user.name}</span>
                        </div>
                    </div>
                `;

                const checkbox = memberItem.querySelector('.group-member-checkbox');
                checkbox.addEventListener('change', (e) => {
                    if (e.target.checked) {
                        selectedGroupMembers.push(user.id);
                    } else {
                        selectedGroupMembers = selectedGroupMembers.filter(id => id !== user.id);
                    }
                });

                groupMembersList.appendChild(memberItem);
            });
        }

        function handleGroupAvatarUpload(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                groupAvatar.innerHTML = `<img src="${e.target.result}" alt="Group Avatar">`;
            };
            reader.readAsDataURL(file);
        }

        function createGroup() {
            const name = groupName.value.trim();
            if (!name) {
                alert('Please enter a group name');
                return;
            }

            if (selectedGroupMembers.length === 0) {
                alert('Please select at least one member');
                return;
            }

            // Create group
            const group = {
                id: 'g' + generateId(),
                name,
                avatar: groupAvatar.querySelector('img')?.src || '',
                members: [
                    { userId: currentUser.id, isAdmin: true },
                    ...selectedGroupMembers.map(id => ({ userId: id, isAdmin: false }))
                ],
                messages: [],
                unreadCount: 0
            };

            groups.push(group);
            chats.push(group);
            saveGroups();
            saveChats();

            // Open the new group chat
            openChat(group);
            closeAllModals();
        }

        function manageCurrentGroup() {
            if (!currentChat || !currentChat.members) return;

            currentManagedGroup = currentChat;
            groupManagementModal.style.display = 'flex';

            // Set group info
            groupManagementTitle.textContent = 'Manage Group';
            groupManagementName.textContent = currentChat.name;
            groupManagementMembersCount.textContent = `${currentChat.members.length} members`;

            if (currentChat.avatar) {
                groupManagementAvatar.innerHTML = `<img src="${currentChat.avatar}" alt="${currentChat.name}">`;
            } else {
                groupManagementAvatar.innerHTML = '<i class="fas fa-users"></i>';
            }

            groupNameInput.value = currentChat.name;

            // Render members
            groupManagementMembers.innerHTML = '';
            currentChat.members.forEach(member => {
                const user = users.find(u => u.id === member.userId);
                if (!user) return;

                const memberItem = document.createElement('div');
                memberItem.className = 'group-member';
                memberItem.innerHTML = `
                    <div class="group-member-info">
                        <div class="avatar avatar-sm">
                            ${user.avatar ? `<img src="${user.avatar}" alt="${user.name}">` : `<i class="fas fa-user"></i>`}
                        </div>
                        <span>${user.name}</span>
                        ${member.isAdmin ? '<span class="admin-badge">Admin</span>' : ''}
                    </div>
                    <div class="group-member-actions">
                        ${!member.isAdmin && currentChat.members.some(m => m.userId === currentUser.id && m.isAdmin) ?
                            `<button class="make-admin-btn" data-user-id="${user.id}">Make Admin</button>` : ''}
                        ${member.userId !== currentUser.id ?
                            `<button class="remove-member-btn" data-user-id="${user.id}">Remove</button>` : ''}
                    </div>
                `;

                groupManagementMembers.appendChild(memberItem);
            });

            // Add event listeners for actions
            document.querySelectorAll('.make-admin-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const userId = e.target.getAttribute('data-user-id');
                    makeGroupAdmin(userId);
                });
            });

            document.querySelectorAll('.remove-member-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const userId = e.target.getAttribute('data-user-id');
                    removeGroupMember(userId);
                });
            });
        }

        function makeGroupAdmin(userId) {
            if (!currentManagedGroup) return;

            const member = currentManagedGroup.members.find(m => m.userId === userId);
            if (member) {
                member.isAdmin = true;
                saveGroups();
                saveChats();
                manageCurrentGroup(); // Refresh the view
            }
        }

        function removeGroupMember(userId) {
            if (!currentManagedGroup) return;

            currentManagedGroup.members = currentManagedGroup.members.filter(m => m.userId !== userId);
            saveGroups();
            saveChats();
            manageCurrentGroup(); // Refresh the view
        }

        function handleGroupPhotoChange(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                currentManagedGroup.avatar = e.target.result;
                groupManagementAvatar.innerHTML = `<img src="${e.target.result}" alt="${currentManagedGroup.name}">`;
            };
            reader.readAsDataURL(file);
        }

        function saveGroupChanges() {
            if (!currentManagedGroup) return;

            const newName = groupNameInput.value.trim();
            if (!newName) {
                alert('Please enter a group name');
                return;
            }

            currentManagedGroup.name = newName;
            saveGroups();
            saveChats();

            // Update UI
            document.getElementById('chat-contact-name').textContent = newName;
            if (currentManagedGroup.avatar) {
                document.getElementById('chat-contact-avatar').innerHTML =
                    `<img src="${currentManagedGroup.avatar}" alt="${newName}">`;
            }

            closeAllModals();
        }

        function saveChats() {
            localStorage.setItem('chats', JSON.stringify(chats));
        }

        function saveGroups() {
            localStorage.setItem('groups', JSON.stringify(groups));
        }

        function saveStatusUpdates() {
            localStorage.setItem('statusUpdates', JSON.stringify(statusUpdates));
        }

        function closeAllModals() {
            document.querySelectorAll('.modal').forEach(modal => {
                modal.style.display = 'none';
            });
            userMenuModal.style.display = 'none';
            chatMenuModal.style.display = 'none';
            emojiPickerContainer.classList.remove('visible');
        }

        function showStatusView() {
            statusView.style.display = 'flex';
            chatArea.style.display = 'none';
            renderStatusList();
        }

        function hideStatusView() {
            statusView.style.display = 'none';
            chatArea.style.display = 'flex';
        }

        function renderStatusList() {
            const statusList = document.querySelector('.status-list');
            statusList.innerHTML = '';

            // Add the "Create New Moment" button at the top
            statusList.innerHTML = `
                <div class="add-status" id="add-status">
                    <div class="add-status-avatar">
                        <i class="fas fa-plus"></i>
                    </div>
                    <div class="add-status-text">Create New Moment</div>
                </div>
            `;

            // Filter status updates to show only from contacts (not blocked users)
            const filteredStatusUpdates = statusUpdates.filter(status =>
                users.some(u => u.id === status.userId && !blockedUsers.includes(u.id))
            );

            if (filteredStatusUpdates.length === 0) {
                statusList.innerHTML += '<div class="empty-content"><p>No moments yet</p></div>';
                return;
            }

            // Group status updates by user
            const statusByUser = {};
            filteredStatusUpdates.forEach(status => {
                if (!statusByUser[status.userId]) {
                    statusByUser[status.userId] = [];
                }
                statusByUser[status.userId].push(status);
            });

            // Sort by most recent
            const sortedUsers = Object.keys(statusByUser).sort((a, b) => {
                const aLastStatus = statusByUser[a][0].timestamp;
                const bLastStatus = statusByUser[b][0].timestamp;
                return new Date(bLastStatus) - new Date(aLastStatus);
            });

            // Render each user's status updates
            sortedUsers.forEach(userId => {
                const user = users.find(u => u.id === userId);
                if (!user) return;

                const statusItem = document.createElement('div');
                statusItem.className = 'status-item';
                statusItem.innerHTML = `
                    <div class="avatar">
                        ${user.avatar ? `<img src="${user.avatar}" alt="${user.name}">` : `<i class="fas fa-user"></i>`}
                    </div>
                    <div class="status-info">
                        <div class="status-name">${user.name}</div>
                        <div class="status-time">${formatTime(statusByUser[userId][0].timestamp)}</div>
                    </div>
                `;

                statusItem.addEventListener('click', () => showUserPosts(user));
                statusList.appendChild(statusItem);
            });
        }

        function showUserPosts(user) {
            currentPostsUser = user;
            currentPostIndex = 0;

            // Set user info
            postsUserName.textContent = user.name;
            if (user.avatar) {
                postsUserAvatar.src = user.avatar;
            } else {
                postsUserAvatar.src = '';
                postsUserAvatar.alt = user.name;
            }

            // Filter posts by this user
            const userPosts = statusUpdates.filter(post => post.userId === user.id);

            // Render posts
            postsContainer.innerHTML = '';
            statusDots.innerHTML = '';

            if (userPosts.length === 0) {
                postsContainer.innerHTML = '<div class="empty-content"><p>No posts yet</p></div>';
            } else {
                userPosts.forEach((post, index) => {
                    // Create status dot
                    const dot = document.createElement('div');
                    dot.className = `status-dot ${index === 0 ? 'active' : ''}`;
                    dot.addEventListener('click', () => scrollToPost(index));
                    statusDots.appendChild(dot);

                    // Create post item
                    const postItem = document.createElement('div');
                    postItem.className = 'post-item';

                    if (post.media.type === 'image') {
                        postItem.innerHTML = `
                            <img src="${post.media.url}" alt="Post image">
                            ${post.caption ? `<div class="post-caption">${post.caption}</div>` : ''}
                        `;
                    } else if (post.media.type === 'video') {
                        postItem.innerHTML = `
                            <video controls autoplay>
                                <source src="${post.media.url}" type="video/mp4">
                                Your browser does not support the video tag.
                            </video>
                            ${post.caption ? `<div class="post-caption">${post.caption}</div>` : ''}
                        `;
                    }

                    postsContainer.appendChild(postItem);
                });

                // Set initial post data
                updatePostInfo(userPosts[0]);
            }

            // Show the modal
            userPostsModal.style.display = 'flex';
            commentSection.style.display = 'none';

            // Scroll to first post
            scrollToPost(0);
        }

        function scrollToPost(index) {
            const userPosts = statusUpdates.filter(post => post.userId === currentPostsUser.id);
            if (index < 0 || index >= userPosts.length) return;

            currentPostIndex = index;
            const postWidth = postsContainer.clientWidth;
            postsContainer.scrollTo({
                left: postWidth * index,
                behavior: 'smooth'
            });

            // Update active dot
            const dots = statusDots.querySelectorAll('.status-dot');
            dots.forEach((dot, i) => {
                dot.classList.toggle('active', i === index);
            });

            // Update post info
            updatePostInfo(userPosts[index]);
        }

        function updatePostInfo(post) {
            likesCountText.textContent = post.likes.length;
            viewsCountText.textContent = post.views;

            // Check if current user liked the post
            const isLiked = post.likes.includes(currentUser.id);
            likePostBtn.innerHTML = isLiked ? '<i class="fas fa-heart"></i>' : '<i class="far fa-heart"></i>';

            // Increment view count if not already viewed by current user
            if (!post.viewedBy) post.viewedBy = [];
            if (!post.viewedBy.includes(currentUser.id)) {
                post.viewedBy.push(currentUser.id);
                post.views = post.viewedBy.length;
                viewsCountText.textContent = post.views;
                saveStatusUpdates();
            }
        }

        function toggleLikePost() {
            const userPosts = statusUpdates.filter(post => post.userId === currentPostsUser.id);
            const currentPost = userPosts[currentPostIndex];

            const likeIndex = currentPost.likes.indexOf(currentUser.id);
            if (likeIndex === -1) {
                // Like the post
                currentPost.likes.push(currentUser.id);
                likePostBtn.innerHTML = '<i class="fas fa-heart"></i>';
            } else {
                // Unlike the post
                currentPost.likes.splice(likeIndex, 1);
                likePostBtn.innerHTML = '<i class="far fa-heart"></i>';
            }

            likesCountText.textContent = currentPost.likes.length;
            saveStatusUpdates();
        }

        function toggleComments() {
            const isCommentsVisible = commentSection.style.display === 'flex';
            commentSection.style.display = isCommentsVisible ? 'none' : 'flex';

            if (!isCommentsVisible) {
                // Load comments when showing the section
                const userPosts = statusUpdates.filter(post => post.userId === currentPostsUser.id);
                const currentPost = userPosts[currentPostIndex];
                renderComments(currentPost.comments);
            }
        }

        function renderComments(comments) {
            commentsList.innerHTML = '';

            if (!comments || comments.length === 0) {
                commentsList.innerHTML = '<div class="empty-content"><p>No comments yet</p></div>';
                return;
            }

            comments.forEach(comment => {
                const user = users.find(u => u.id === comment.userId);
                if (!user) return;

                const commentDiv = document.createElement('div');
                commentDiv.className = 'comment';
                commentDiv.innerHTML = `
                    <div class="comment-user">
                        <div class="comment-user-avatar">
                            ${user.avatar ? `<img src="${user.avatar}" alt="${user.name}">` : `<i class="fas fa-user"></i>`}
                        </div>
                        <span class="comment-user-name">${user.name}</span>
                    </div>
                    <div class="comment-text">${comment.text}</div>
                    <div class="comment-time">${formatTime(comment.timestamp)}</div>
                `;
                commentsList.appendChild(commentDiv);
            });

            // Scroll to bottom
            commentsList.scrollTop = commentsList.scrollHeight;
        }

        function addCommentToPost() {
            const commentText = commentInput.value.trim();
            if (!commentText) return;

            const userPosts = statusUpdates.filter(post => post.userId === currentPostsUser.id);
            const currentPost = userPosts[currentPostIndex];

            const newComment = {
                userId: currentUser.id,
                text: commentText,
                timestamp: new Date().toISOString()
            };

            if (!currentPost.comments) currentPost.comments = [];
            currentPost.comments.push(newComment);
            saveStatusUpdates();

            // Update UI
            renderComments(currentPost.comments);
            commentInput.value = '';
            commentInput.style.height = 'auto';
        }

        function showCreateStatusModal() {
            createStatusModal.style.display = 'flex';
            statusMediaPreview.innerHTML = '<i class="fas fa-camera"></i>';
            statusCaption.value = '';
            statusMediaInput.value = '';
        }

        function handleStatusMediaUpload(e) {
            const file = e.target.files[0];
            if (!file) return;

            const fileType = file.type.split('/')[0];
            const isImage = fileType === 'image';
            const isVideo = fileType === 'video';

            if (!isImage && !isVideo) {
                alert('Please select an image or video file');
                return;
            }

            // Check file size (max 15MB) {Really important I should work on it to make it work}
            if (file.size > 15 * 1024 * 1024) {
                alert('File size should be less than 15MB');
                return;
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                if (isImage) {
                    statusMediaPreview.innerHTML = `<img src="${e.target.result}" alt="Status image">`;
                } else if (isVideo) {
                    statusMediaPreview.innerHTML = `
                        <video controls>
                            <source src="${e.target.result}" type="${file.type}">
                            Your browser does not support the video tag.
                        </video>
                    `;
                }
            };
            reader.readAsDataURL(file);
        }

        function postStatusUpdate() {
            const caption = statusCaption.value.trim();
            const file = statusMediaInput.files[0];

            if (!file) {
                alert('Please select a photo or video');
                return;
            }

            const fileType = file.type.split('/')[0];
            const isImage = fileType === 'image';
            const isVideo = fileType === 'video';

            const reader = new FileReader();
            reader.onload = function(e) {
                const statusUpdate = {
                    id: generateId(),
                    userId: currentUser.id,
                    media: {
                        type: isImage ? 'image' : 'video',
                        url: e.target.result
                    },
                    caption,
                    timestamp: new Date().toISOString(),
                    views: 0,
                    likes: [],
                    comments: [],
                    viewedBy: []
                };

                statusUpdates.push(statusUpdate);
                saveStatusUpdates();
                closeAllModals();

                // Update status view
                if (statusView.style.display === 'flex') {
                    renderStatusList();
                }
            };
            reader.readAsDataURL(file);
        }

        function toggleUserMenu() {
            if (userMenuModal.style.display === 'block') {
                userMenuModal.style.display = 'none';
            } else {
                userMenuModal.style.display = 'block';
            }
        }

        function toggleChatMenu() {
            if (chatMenuModal.style.display === 'block') {
                chatMenuModal.style.display = 'none';
            } else {
                chatMenuModal.style.display = 'block';
            }
        }

        function showProfileModal() {
            profileModal.style.display = 'flex';
            renderProfileModal();
        }

        function renderProfileModal() {
            if (!currentUser) return;

            profileName.textContent = currentUser.name;
            profileStatus.textContent = currentUser.status || 'Hey there! I am using NexaChat';

            if (currentUser.avatar) {
                profileAvatarImg.src = currentUser.avatar;
                profileAvatarImg.style.display = 'block';
            } else {
                profileAvatarImg.style.display = 'none';
            }

            profileNameInput.value = currentUser.name;
            profileEmail.value = currentUser.email;
            profileStatusInput.value = currentUser.status || '';

            // Render blocked users
            renderBlockedUsers();
        }

        function renderBlockedUsers() {
            blockedUsersList.innerHTML = '';

            if (blockedUsers.length === 0) {
                blockedUsersList.innerHTML = '<p>No blocked users</p>';
                return;
            }

            blockedUsers.forEach(userId => {
                const user = users.find(u => u.id === userId);
                if (!user) return;

                const blockedUserDiv = document.createElement('div');
                blockedUserDiv.className = 'blocked-user';
                blockedUserDiv.innerHTML = `
                    <div class="blocked-user-info">
                        <div class="avatar avatar-sm">
                            ${user.avatar ? `<img src="${user.avatar}" alt="${user.name}">` : `<i class="fas fa-user"></i>`}
                        </div>
                        <span>${user.name}</span>
                    </div>
                    <button class="unblock-btn" data-user-id="${user.id}">Unblock</button>
                `;

                blockedUserDiv.querySelector('.unblock-btn').addEventListener('click', () => unblockUser(user.id));
                blockedUsersList.appendChild(blockedUserDiv);
            });
        }

        function unblockUser(userId) {
            blockedUsers = blockedUsers.filter(id => id !== userId);
            localStorage.setItem('blockedUsers', JSON.stringify(blockedUsers));
            renderBlockedUsers();

            // Update contacts list if needed
            renderContacts();
        }

        function handleProfileAvatarUpload(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                currentUser.avatar = e.target.result;
                profileAvatarImg.src = e.target.result;
                profileAvatarImg.style.display = 'block';

                // Update current user avatar in UI
                currentUserAvatar.src = e.target.result;
                currentUserAvatar.style.display = 'block';

                // Update in chats if needed
                saveCurrentUser();
            };
            reader.readAsDataURL(file);
        }

        function saveProfile() {
            const newName = profileNameInput.value.trim();
            const newStatus = profileStatusInput.value.trim();
            const newPassword = profilePassword.value.trim();

            if (!newName) {
                alert('Please enter your name');
                return;
            }

            // Update current user
            currentUser.name = newName;
            currentUser.status = newStatus;

            if (newPassword) {
                currentUser.password = newPassword;
            }

            saveCurrentUser();
            closeAllModals();

            // Update UI
            renderCurrentUser();
            renderChats();
        }

        function saveCurrentUser() {
            localStorage.setItem('currentUser', JSON.stringify(currentUser));

            // Update in users array
            const userIndex = users.findIndex(u => u.id === currentUser.id);
            if (userIndex !== -1) {
                users[userIndex] = currentUser;
                localStorage.setItem('users', JSON.stringify(users));
            }
        }

        function blockCurrentUser() {
            if (!currentChat || !currentChat.userId) return;

            if (blockedUsers.includes(currentChat.userId)) {
                alert('This user is already blocked');
                return;
            }

            if (confirm(`Are you sure you want to block ${document.getElementById('chat-contact-name').textContent}?`)) {
                blockedUsers.push(currentChat.userId);
                localStorage.setItem('blockedUsers', JSON.stringify(blockedUsers));

                // Close the chat
                currentChat = null;
                emptyChat.style.display = 'flex';
                chatHeader.style.display = 'none';
                messagesContainer.style.display = 'none';
                messageInputContainer.style.display = 'none';

                // Update UI
                renderContacts();
                renderChats();
                closeAllModals();
            }
        }

        function deleteCurrentChat() {
            if (!currentChat) return;

            const chatName = currentChat.userId ?
                users.find(u => u.id === currentChat.userId)?.name :
                currentChat.name;

            if (confirm(`Are you sure you want to delete your conversation with ${chatName}?`)) {
                // Remove chat from chats array
                chats = chats.filter(c => c.id !== currentChat.id);
                saveChats();

                // If it's a group, remove from groups array
                if (currentChat.members) {
                    groups = groups.filter(g => g.id !== currentChat.id);
                    saveGroups();
                }

                // Close the chat
                currentChat = null;
                emptyChat.style.display = 'flex';
                chatHeader.style.display = 'none';
                messagesContainer.style.display = 'none';
                messageInputContainer.style.display = 'none';

                // Update UI
                renderChats();
                closeAllModals();
            }
        }

        function startVoiceCall() {
            if (!currentChat) return;

            // In a real app, you would initiate a WebRTC call here
            alert(`Starting voice call with ${document.getElementById('chat-contact-name').textContent}`);

            // For demo, show the call UI
            videoCallModal.style.display = 'flex';
            remoteVideo.style.display = 'none';
            document.querySelector('.remote-video').innerHTML = `
                <div class="call-user-info">
                    <div class="avatar avatar-xl">
                        ${document.getElementById('chat-contact-avatar').innerHTML}
                    </div>
                    <h3>${document.getElementById('chat-contact-name').textContent}</h3>
                    <p>Calling...</p>
                </div>
            `;
        }

        function startVideoCall() {
            if (!currentChat) return;

            function startVideoCall() {
                if (!currentChat) return;

                // Simple WebRTC initialization without complex setup
                try {
                    // Create peer connection
                    const pc = new RTCPeerConnection();

                    // Get user media
                    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
                        .then(stream => {
                            // Add stream to peer connection
                            stream.getTracks().forEach(track => pc.addTrack(track, stream));

                            // Create and set local description
                            pc.createOffer().then(offer => pc.setLocalDescription(offer));

                            console.log('WebRTC call initiated');
                        })
                        .catch(err => {
                            console.error('Error accessing media devices:', err);
                        });

                } catch (error) {
                    console.error('WebRTC not supported:', error);
                }

                alert(`Starting video call with ${document.getElementById('chat-contact-name').textContent}`);
            }

            // For demo, show the call UI
            videoCallModal.style.display = 'flex';
            remoteVideo.style.display = 'block';
            document.querySelector('.remote-video').innerHTML = `
                <video id="remote-stream" autoplay playsinline></video>
                <div class="call-user-info">
                    <h3>${document.getElementById('chat-contact-name').textContent}</h3>
                    <p>Calling...</p>
                </div>
            `;

            // Simulate getting local video stream
            navigator.mediaDevices.getUserMedia({ video: true, audio: true })
                .then(stream => {
                    localStream = stream;
                    localVideo.srcObject = stream;
                })
                .catch(err => {
                    console.error('Error accessing media devices:', err);
                    alert('Could not access camera/microphone');
                });
        }

        function toggleMute() {
            isMuted = !isMuted;
            if (localStream) {
                localStream.getAudioTracks().forEach(track => {
                    track.enabled = !isMuted;
                });
            }
            muteCallBtn.innerHTML = isMuted ? '<i class="fas fa-microphone-slash"></i>' : '<i class="fas fa-microphone"></i>';
        }

        function toggleVideo() {
            isVideoOff = !isVideoOff;
            if (localStream) {
                localStream.getVideoTracks().forEach(track => {
                    track.enabled = !isVideoOff;
                });
            }
            videoToggleBtn.innerHTML = isVideoOff ? '<i class="fas fa-video-slash"></i>' : '<i class="fas fa-video"></i>';
        }

        function endCall() {
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                localStream = null;
            }
            videoCallModal.style.display = 'none';
        }

        function toggleDarkMode() {
            isDarkMode = !isDarkMode;
            document.body.classList.toggle('dark-mode', isDarkMode);
            localStorage.setItem('darkMode', isDarkMode);

            // Update button icon
            toggleDarkModeBtn.innerHTML = isDarkMode ?
                '<i class="fas fa-sun"></i> Light Mode' :
                '<i class="fas fa-moon"></i> Dark Mode';
        }

        async function logout() {
            try {
                await fetch('/api/logout', { method: 'POST' });
                currentUser = null;
                showAuth();
                closeAllModals();
            } catch (error) {
                console.error('Logout failed:', error);
            }
        }

        // Expose some functions to the global scope for HTML onclick attributes
        window.showImagePreview = showImagePreview;
        window.startChat = startChat;
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# API Routes
@app.route('/api/session', methods=['GET'])
def get_session():
    user_id = session.get('user_id')
    if user_id and user_id in users:
        return jsonify({
            'user': users[user_id],
            'users': list(users.values())
        })
    return jsonify({'user': None})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Find user
    for user_id, user in users.items():
        if user['email'] == email and user['password'] == password:
            session['user_id'] = user_id
            user['lastSeen'] = datetime.now().isoformat()
            online_users.add(user_id)
            return jsonify({
                'user': user,
                'users': list(users.values())
            })

    return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    avatar = data.get('avatar', '')

    # Check if user exists
    for user in users.values():
        if user['email'] == email:
            return jsonify({'error': 'User already exists'}), 400

    # Create new user
    user_id = str(uuid.uuid4())
    new_user = {
        'id': user_id,
        'name': name,
        'email': email,
        'password': password,
        'avatar': avatar,
        'status': 'Hey there! I am using NexaChat',
        'lastSeen': datetime.now().isoformat()
    }

    users[user_id] = new_user
    session['user_id'] = user_id
    online_users.add(user_id)

    # Create sample chats for new user
    create_sample_chats(user_id)

    return jsonify({
        'user': new_user,
        'users': list(users.values())
    })

@app.route('/api/user/data', methods=['GET'])
def get_user_data():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user_chats = chats.get(user_id, [])
    user_groups = groups.get(user_id, [])
    user_status = status_updates.get(user_id, [])
    user_blocked = blocked_users.get(user_id, [])

    return jsonify({
        'users': list(users.values()),
        'chats': user_chats,
        'groups': user_groups,
        'statusUpdates': user_status,
        'blockedUsers': user_blocked
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    user_id = session.pop('user_id', None)
    if user_id in online_users:
        online_users.remove(user_id)
        if user_id in users:
            users[user_id]['lastSeen'] = datetime.now().isoformat()
    return jsonify({'success': True})

# WebSocket events
@socketio.on('connect')
def handle_connect():
    user_id = session.get('user_id')
    if user_id:
        online_users.add(user_id)
        emit('user_online', {'userId': user_id}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    user_id = session.get('user_id')
    if user_id in online_users:
        online_users.remove(user_id)
        if user_id in users:
            users[user_id]['lastSeen'] = datetime.now().isoformat()
        emit('user_offline', {'userId': user_id}, broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    sender_id = session.get('user_id')
    if not sender_id:
        return

    chat_id = data.get('chatId')
    recipient_id = data.get('recipientId')
    message = data.get('message')

    # Store message
    message_id = str(uuid.uuid4())
    new_message = {
        'id': message_id,
        'sender': sender_id,
        'content': message,
        'timestamp': datetime.now().isoformat(),
        'status': 'sent'
    }

    # Add to chats
    if chat_id not in chats.get(sender_id, []):
        if sender_id not in chats:
            chats[sender_id] = []
        chats[sender_id].append(chat_id)

    # Emit to recipient
    emit('new_message', {
        'chatId': chat_id,
        'message': new_message
    }, room=recipient_id)

@socketio.on('typing')
def handle_typing(data):
    user_id = session.get('user_id')
    if not user_id:
        return

    chat_id = data.get('chatId')
    is_typing = data.get('isTyping')

    emit('user_typing', {
        'chatId': chat_id,
        'userId': user_id,
        'isTyping': is_typing
    }, room=chat_id)

# Helper functions
def create_sample_chats(user_id):
    """Create sample chats for new user"""
    if len(users) < 2:
        return

    # Get first other user
    other_user_id = next((uid for uid in users.keys() if uid != user_id), None)
    if not other_user_id:
        return

    chat_id = str(uuid.uuid4())
    sample_messages = [
        {
            'id': str(uuid.uuid4()),
            'sender': other_user_id,
            'content': 'Welcome to NexaChat! 👋',
            'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
            'status': 'read'
        },
        {
            'id': str(uuid.uuid4()),
            'sender': user_id,
            'content': 'Thanks! Great to be here!',
            'timestamp': datetime.now().isoformat(),
            'status': 'sent'
        }
    ]

    chat = {
        'id': chat_id,
        'userId': other_user_id,
        'messages': sample_messages,
        'unreadCount': 0
    }

    chats[user_id] = [chat]

    # Also add to other user's chats
    if other_user_id not in chats:
        chats[other_user_id] = []

    other_chat = {
        'id': chat_id,
        'userId': user_id,
        'messages': sample_messages,
        'unreadCount': 1
    }
    chats[other_user_id].append(other_chat)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)

admin account

username: admin
password: jLD!>54t

# eLearning Web Application
[Description of your project]

## License
This project is licensed under the [License Name] - see the [LICENSE](LICENSE) file for details.

UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM chat_message) WHERE name="chat_message"
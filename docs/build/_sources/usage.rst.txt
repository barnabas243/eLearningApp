Usage
=====

.. _installation:

Installation
------------

Before you begin, ensure that Docker is installed on your system. If you haven't installed Docker yet, please visit `Docker's official website <https://www.docker.com/get-started/>`_ and follow the instructions to download and install Docker for your operating system.

Once Docker is installed, follow these steps to run the eLearningApp:

1. **Download the eLearningApp zip file** and extract its contents to a directory of your choice.

2. **Open a terminal or command prompt**, and navigate to the directory containing the extracted eLearningApp files:

   .. code-block:: bash
      :linenos:

      cd eLearningApp/

3. **Build and run the Docker containers** using Docker Compose:

   .. code-block:: bash
      :linenos:

      docker-compose up --build

   This command will build the Docker images and start the containers for the eLearningApp and its dependencies.

4. **Access the application**:

   Once the containers are up and running, you can access the eLearningApp in your web browser at https://localhost.

   .. hint::

      If you encounter any issues during installation, please refer to the troubleshooting section in the documentation.

---

Alternatively, you can run the eLearningApp using Django's built-in development server. Follow these steps:

Django Installation
--------------------

Before you begin, ensure that Python and Django are installed on your system. If you haven't installed Django yet, you can install it using pip:

.. code-block:: console

   pip install django

Once Django is installed, follow these steps to set up and run the eLearningApp:

1. **Download the eLearningApp zip file** and extract its contents to a directory of your choice.

2. **Open a terminal or command prompt**, and navigate to the directory containing the extracted eLearningApp files:

   .. code-block:: bash
      :linenos:

      cd path/to/eLearningApp

3. **Install the dependencies** using the following command:

   .. code-block:: bash
      :linenos:

      pip install -r requirements.txt

   This command will install all the required Python packages for the eLearningApp.

4. **Apply database migrations** using the following command:

   .. code-block:: bash
      :linenos:

      python manage.py migrate

   This command will create the necessary database tables for the eLearningApp.

5. **Run the Django development server** using the following command:

   .. code-block:: bash
      :linenos:

      python manage.py runserver

   This command will start the Django development server, and you can access the eLearningApp in your web browser at http://localhost:8000.

For more information on how to use the eLearningApp, please refer to the documentation.

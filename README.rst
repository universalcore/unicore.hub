unicore.hub
===========

Installation
------------

.. code-block:: bash

    $ virtualenv ve
    $ source ve/bin/activate
    (ve)$ pip install -e .

Running `unicore.hub.service`
-----------------------------

Run the development server using:

.. code-block:: bash

    (ve)$ alembic upgrade head
    (ve)$ pserve development.ini --reload


Running tests
-------------

.. code-block:: bash

    (ve)$ py.test unicore/hub/

Using the APIs
--------------

The App API
***********

To query the App API, create an app with management permissions:

.. code-block:: bash

    (ve)$ hubservice development.ini create_app "Foo App" --group "group:apps_manager"
    App 'Foo App' has been created and assigned to ('group:apps_manager',)
    App identifier is '8fb79adb1a9340c390f32bb6c27ebc39'
    App password is 'BZPHmoUeQKZ2q5KHRNqb'

Use the management app's credentials to create, view and edit apps:

.. code-block:: bash

    (ve)$ curl --user 8fb79adb1a9340c390f32bb6c27ebc39:BZPHmoUeQKZ2q5KHRNqb -H "Content-Type: application/json" -d '{"title": "Foo"}' http://localhost:8000/apps
    {"password": "Bq4JlaOxXx9atOFBHpHh", "title": "Foo", "uuid": "ba0529456a9a4602a85ccca6c35f4f38", "groups": []}
    (ve)$ curl --user 8fb79adb1a9340c390f32bb6c27ebc39:BZPHmoUeQKZ2q5KHRNqb http://localhost:8000/apps/ba0529456a9a4602a85ccca6c35f4f38
    {"title": "Foo", "uuid": "ba0529456a9a4602a85ccca6c35f4f38", "groups": []}
    (ve)$ curl --user 8fb79adb1a9340c390f32bb6c27ebc39:BZPHmoUeQKZ2q5KHRNqb -d '{"title": "New Foo"}' -XPUT http://localhost:8000/apps/ba0529456a9a4602a85ccca6c35f4f38
    {"title": "New Foo", "uuid": "ba0529456a9a4602a85ccca6c35f4f38", "groups": []}

A new app's password is only returned once - on creation. To reset the password, use the `/apps/{user_id}/reset_password` endpoint:

.. code-block:: bash

    (ve)$ curl --user 8fb79adb1a9340c390f32bb6c27ebc39:BZPHmoUeQKZ2q5KHRNqb -XPUT http://localhost:8000/apps/ba0529456a9a4602a85ccca6c35f4f38/reset_password
    {"password": "71USAvzCZ2YUOsGqzuA1", "title": "New Foo", "uuid": "ba0529456a9a4602a85ccca6c35f4f38", "groups": []}

**Note:** The app created above does not have management permissions. This means it can only view and edit its own data, and it cannot create apps.

The User API
************

The User API can be queried using an app's credentials. Every app can create, view and edit its own user data. Aside from management apps, an app cannot access the user data of another app.

Let's use the app created above to store and retrieve user data:

.. code-block:: bash

    (ve)$ curl --user ba0529456a9a4602a85ccca6c35f4f38:71USAvzCZ2YUOsGqzuA1 -d '{"display_name": "Foo Bar"}' http://localhost:8000/users/cfdfbfc6ca064a48b77f0dc615e0841d
    {"success": true}
    (ve)$ curl --user ba0529456a9a4602a85ccca6c35f4f38:71USAvzCZ2YUOsGqzuA1 http://localhost:8000/users/cfdfbfc6ca064a48b77f0dc615e0841d
    {"display_name": "Foo Bar"}

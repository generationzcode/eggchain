Hello Replit user,

We've performed an automatic upgrade to your repl due to a found
vulnerability our Django template. There's a hardcoded secret value
in settings.py. To properly secure the web server, a user should
set up a secret environment variable and have the code read from it.
Most users do not take this step, which we do not blame you,
since we have not this step obvious at all. Nevertheless, the vulnerability
is severe as if the secret is obtained, an anonymous user can intercept and
decode authenticated requests as well as impersonate authenticated users.
For this reason, we decided to take action to protect our users.

The upgrade process is as follows:

0. if the hardcoded value is found in your code, we perform the update
1. we modify settings.py to use an environment variable named SECRET_KEY
2. we add a new secret environment variable to your repl named SECRET_KEY
containing a randomly generated value, which is different for each repl

Just in case our automatic procedure makes a mistake, we've backed up
each file we overwrite in this backup directory. If you need to
revert our fix, you have the means to do so. However, we strongly
encourage you to generate your own secret value within the "Secrets (environment variables)"
tab instead of hardcoding the value.

If you have questions and/or need help, feel free to contact support.

Thank you for reading,
- The Replit Staff


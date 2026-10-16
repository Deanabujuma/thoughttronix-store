"""The development email backend: Django's console backend, made readable.

The stock console backend prints each email as it would go over the wire.
Any body line over 78 characters — a password-reset link always is one —
forces quoted-printable, which splits the line with an "=" soft break, so
a link copied from the terminal is broken. Printing under a policy with
no line limit that allows 8-bit text leaves the body exactly as written.
A character the terminal can't show (a cp1252 Windows console, say) is
replaced rather than raised, so printing an email never breaks a request.
"""

import email.policy

from django.core.mail.backends import console

READABLE = email.policy.default.clone(cte_type="8bit", max_line_length=None)


class EmailBackend(console.EmailBackend):
    """Write each message to the console with its body as plain text."""

    def write_message(self, message):
        msg_data = message.message(policy=READABLE).as_bytes().decode()
        encoding = getattr(self.stream, "encoding", None) or "utf-8"
        msg_data = msg_data.encode(encoding, "replace").decode(encoding)
        self.stream.write(f"{msg_data}\n")
        self.stream.write("-" * 79)
        self.stream.write("\n")

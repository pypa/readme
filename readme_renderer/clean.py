# Copyright 2014 Donald Stufft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import, division, print_function

import functools
import typing

import bleach
import bleach.callbacks
import bleach.linkifier
import bleach.sanitizer


ALLOWED_TAGS = [
    # Bleach Defaults
    "a", "abbr", "acronym", "b", "blockquote", "code", "em", "i", "li", "ol",
    "strong", "ul",

    # Custom Additions
    "br", "caption", "cite", "col", "colgroup", "dd", "del", "details", "div",
    "dl", "dt", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "img", "p", "pre",
    "span", "sub", "summary", "sup", "table", "tbody", "td", "th", "thead",
    "tr", "tt", "kbd", "var", "input",
]

ALLOWED_ATTRIBUTES = {
    # Bleach Defaults
    "a": ["href", "title"],
    "abbr": ["title"],
    "acronym": ["title"],

    # Custom Additions
    "*": ["id"],
    "hr": ["class"],
    "img": ["src", "width", "height", "alt", "align", "class"],
    "span": ["class"],
    "th": ["align"],
    "td": ["align"],
    "div": ["align"],
    "h1": ["align"],
    "h2": ["align"],
    "h3": ["align"],
    "h4": ["align"],
    "h5": ["align"],
    "h6": ["align"],
    "code": ["class"],
    "p": ["align"],
    "ol": ["start"],
    "input": ["type", "checked", "disabled"],
}


class DisabledCheckboxInputsFilter:
    def __init__(self, source: typing.Any) -> None:
        self.source = source

    def __iter__(self) -> typing.Iterator[typing.Dict[str, typing.Optional[str]]]:
        for token in self.source:
            if token.get("name") == "input":
                # only allow disabled checkbox inputs
                is_checkbox, is_disabled, unsafe_attrs = False, False, False
                for (_, attrname), value in token.get("data", {}).items():
                    if attrname == "type" and value == "checkbox":
                        is_checkbox = True
                    elif attrname == "disabled":
                        is_disabled = True
                    elif attrname != "checked":
                        unsafe_attrs = True
                        break
                if is_checkbox and is_disabled and not unsafe_attrs:
                    yield token
            else:
                yield token

    def __getattr__(self, name: str) -> typing.Any:
        return getattr(self.source, name)


def clean(
    html: str,
    tags: typing.Optional[typing.List[str]] = None,
    attributes: typing.Optional[typing.Dict[str, typing.List[str]]] = None
) -> typing.Optional[str]:
    if tags is None:
        tags = ALLOWED_TAGS
    if attributes is None:
        attributes = ALLOWED_ATTRIBUTES

    # Clean the output using Bleach
    cleaner = bleach.sanitizer.Cleaner(
        tags=tags,
        attributes=attributes,
        filters=[
            # Bleach Linkify makes it easy to modify links, however, we will
            # not be using it to create additional links.
            functools.partial(
                bleach.linkifier.LinkifyFilter,
                callbacks=[
                    lambda attrs, new: attrs if not new else None,
                    bleach.callbacks.nofollow,
                ],
                skip_tags=["pre"],
                parse_email=False,
            ),
            DisabledCheckboxInputsFilter,
        ],
    )
    try:
        cleaned = cleaner.clean(html)
        return cleaned
    except ValueError:
        return None

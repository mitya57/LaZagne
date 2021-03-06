#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lazagne.config.module_info import ModuleInfo
from lazagne.config import homes
import traceback


class Libsecret(ModuleInfo):
    def __init__(self):
        ModuleInfo.__init__(self, 'libsecret', 'wallet')

    def run(self):
        items = []
        visited = set()
        try:
            import dbus
            import secretstorage
            import datetime
        except ImportError as e:
            self.error('libsecret: {0}'.format(e))
            return []

        for _, session in homes.sessions():
            try:
                # List bus connection names
                bus = dbus.bus.BusConnection(session)
                if 'org.freedesktop.secrets' not in [str(x) for x in bus.list_names()]:
                    continue
            except Exception:
                self.error(traceback.format_exc())
                continue

            collections = None
            try:
                # Python 2.7
                collections = list(secretstorage.collection.get_all_collections(bus))
            except Exception:
                pass

            if not collections:
                try:
                    # Python 3
                    from jeepney.integrate.blocking import connect_and_authenticate
                    bus = connect_and_authenticate(session)
                    collections = secretstorage.get_all_collections(bus)
                except Exception:
                    self.error(traceback.format_exc())
                    continue

            for collection in collections:
                if collection.is_locked():
                    continue

                label = collection.get_label()
                if label in visited:
                    continue

                visited.add(label)

                try:
                    storage = collection.get_all_items()
                except Exception:
                    self.error(traceback.format_exc())
                    continue

                for item in storage:
                    values = {
                        'created': str(datetime.datetime.fromtimestamp(item.get_created())),
                        'modified': str(datetime.datetime.fromtimestamp(item.get_modified())),
                        'content-type': item.get_secret_content_type(),
                        'label': item.get_label(),
                        'Password': item.get_secret(),
                        'collection': label,
                    }

                    # for k, v in item.get_attributes().iteritems():
                    # 	values[unicode(k)] = unicode(v)
                    items.append(values)

            try:
                bus.flush()
                bus.close()
            except Exception:
                pass

        return items

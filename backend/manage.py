#!/usr/bin/env python
import os, sys
if __name__ == '__main__':
    # La variabile DJANGO_SETTINGS_MODULE viene impostata dall'ambiente
    # (dal render.yaml per il deploy o da un file .env per lo sviluppo)
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

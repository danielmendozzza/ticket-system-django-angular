from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


def _col_name(index):
    name = ''
    while index > 0:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def _sheet_xml(rows, autofilter_ref=None):
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        '<sheetData>',
    ]

    for row_idx, row in enumerate(rows, start=1):
        lines.append(f'<row r="{row_idx}">')
        for col_idx, value in enumerate(row, start=1):
            cell_ref = f'{_col_name(col_idx)}{row_idx}'
            text = '' if value is None else escape(str(value))
            lines.append(
                f'<c r="{cell_ref}" t="inlineStr"><is><t>{text}</t></is></c>'
            )
        lines.append('</row>')

    lines.append('</sheetData>')
    if autofilter_ref:
        lines.append(f'<autoFilter ref="{autofilter_ref}"/>')
    lines.append('</worksheet>')
    return ''.join(lines)


def _format_datetime(value):
    return value.strftime('%d/%m/%Y %H:%M') if value else ''


def _format_duration(start, end):
    if not start or not end:
        return ''

    total_minutes = int((end - start).total_seconds() // 60)
    if total_minutes < 0:
        return ''

    hours, minutes = divmod(total_minutes, 60)
    return f'{hours}h {minutes}m'


def _fuera_sla(ticket):
    if not ticket.fecha_limite:
        return 'No'

    if ticket.fecha_conclusion:
        return 'Si' if ticket.fecha_conclusion > ticket.fecha_limite else 'No'

    return 'Si' if ticket.esta_vencido else 'No'


def build_ticket_report_workbook(tickets, desde, hasta, filtros):
    rows = [
        ['Reporte detallado de tickets'],
        ['Desde', _format_datetime(desde), 'Hasta', _format_datetime(hasta)],
        [
            'Tecnico',
            filtros.get('tecnico') or 'Todos',
            'Sucursal',
            filtros.get('sucursal') or 'Todas',
            'Estado',
            filtros.get('estado') or 'Todos',
        ],
        [],
        [
            'ID',
            'Mes',
            'Tecnico',
            'Sucursal',
            'Zona',
            'Incidencia',
            'Descripción',
            'Equipo',
            'Prioridad',
            'Estado',
            'Fecha inicio',
            'Fecha limite',
            'Fecha conclusion',
            'Tiempo resolucion',
            'Fuera SLA',
            'Evidencia cargada',
            'Comentario técnico',
        ],
    ]

    for ticket in tickets:
        rows.append([
            ticket.id,
            ticket.fecha_inicio.strftime('%m/%Y') if ticket.fecha_inicio else '',
            ticket.tecnico.user.username if ticket.tecnico_id else 'Sin asignar',
            ticket.sucursal.nombre if ticket.sucursal_id else '',
            ticket.sucursal.area.nombre if ticket.sucursal_id and ticket.sucursal.area_id else '',
            ticket.titulo,
            ticket.descripcion,
            ticket.equipo or '',
            ticket.get_prioridad_display(),
            ticket.get_estado_display(),
            _format_datetime(ticket.fecha_inicio),
            _format_datetime(ticket.fecha_limite),
            _format_datetime(ticket.fecha_conclusion),
            _format_duration(ticket.fecha_inicio, ticket.fecha_conclusion),
            _fuera_sla(ticket),
            'Si' if ticket.evidencia_cierre else 'No',
            ticket.comentario_tecnico or '',
        ])

    workbook_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <sheets>
  <sheet name="Tickets" sheetId="1" r:id="rId1"/>
 </sheets>
</workbook>'''

    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''

    root_rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

    content_types_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="xml" ContentType="application/xml"/>
 <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
 <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>'''

    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types_xml)
        zf.writestr('_rels/.rels', root_rels_xml)
        zf.writestr('xl/workbook.xml', workbook_xml)
        zf.writestr('xl/_rels/workbook.xml.rels', rels_xml)
        zf.writestr('xl/worksheets/sheet1.xml', _sheet_xml(rows, f'A5:Q{len(rows)}'))

    return output.getvalue()


def build_comparison_workbook(base_summary, compare_summary):
    rows = [
        ['Comparativo mensual de tickets'],
        [],
        ['Indicador', base_summary['label'], compare_summary['label'] if compare_summary else 'Sin comparación'],
        ['Total tickets', base_summary['total_tickets'], compare_summary['total_tickets'] if compare_summary else ''],
        ['Tickets vencidos', base_summary['tickets_vencidos'], compare_summary['tickets_vencidos'] if compare_summary else ''],
        [
            'Técnico con más resueltos',
            (base_summary['tecnico_con_mas_incidencias_resueltas'] or {}).get('tecnico__user__username', 'Sin datos'),
            (compare_summary['tecnico_con_mas_incidencias_resueltas'] or {}).get('tecnico__user__username', 'Sin datos')
            if compare_summary else '',
        ],
        [
            'Técnico con menor carga',
            (base_summary['tecnico_con_menos_incidencias'] or {}).get('tecnico__user__username', 'Sin datos'),
            (compare_summary['tecnico_con_menos_incidencias'] or {}).get('tecnico__user__username', 'Sin datos')
            if compare_summary else '',
        ],
        [],
        ['Ranking tecnicos base'],
        ['Tecnico', 'Total', 'Resueltos', 'Pendientes'],
    ]

    for item in base_summary['ranking_tecnicos']:
        rows.append([
            item.get('tecnico__user__username') or 'Sin asignar',
            item.get('total', 0),
            item.get('resueltos', 0),
            item.get('pendientes', 0),
        ])

    if compare_summary:
        rows.extend([
            [],
            ['Ranking técnicos comparación'],
            ['Tecnico', 'Total', 'Resueltos', 'Pendientes'],
        ])
        for item in compare_summary['ranking_tecnicos']:
            rows.append([
                item.get('tecnico__user__username') or 'Sin asignar',
                item.get('total', 0),
                item.get('resueltos', 0),
                item.get('pendientes', 0),
            ])

    rows.extend([
        [],
        ['Sucursales con más incidencias base'],
        ['Sucursal', 'Total'],
    ])
    for item in base_summary['sucursales_con_mas_incidencias']:
        rows.append([item.get('sucursal__nombre', ''), item.get('total', 0)])

    if compare_summary:
        rows.extend([
            [],
            ['Sucursales con más incidencias comparación'],
            ['Sucursal', 'Total'],
        ])
        for item in compare_summary['sucursales_con_mas_incidencias']:
            rows.append([item.get('sucursal__nombre', ''), item.get('total', 0)])

    workbook_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <sheets>
  <sheet name="Comparativo" sheetId="1" r:id="rId1"/>
 </sheets>
</workbook>'''

    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''

    root_rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

    content_types_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="xml" ContentType="application/xml"/>
 <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
 <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>'''

    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types_xml)
        zf.writestr('_rels/.rels', root_rels_xml)
        zf.writestr('xl/workbook.xml', workbook_xml)
        zf.writestr('xl/_rels/workbook.xml.rels', rels_xml)
        zf.writestr('xl/worksheets/sheet1.xml', _sheet_xml(rows))

    return output.getvalue()


def build_tickets_workbook(tickets):
    rows = [
        ['Tickets exportados desde Django admin'],
        [],
        [
            'ID',
            'Título',
            'Descripción',
            'Equipo',
            'Prioridad',
            'Estado',
            'Sucursal',
            'Zona',
            'Tecnico',
            'Fecha creacion',
            'Fecha inicio',
            'Fecha limite',
            'Fecha conclusion',
            'Comentario técnico',
        ],
    ]

    for ticket in tickets:
        rows.append([
            ticket.id,
            ticket.titulo,
            ticket.descripcion,
            ticket.equipo or '',
            ticket.get_prioridad_display(),
            ticket.get_estado_display(),
            ticket.sucursal.nombre if ticket.sucursal_id else '',
            ticket.sucursal.area.nombre if ticket.sucursal_id and ticket.sucursal.area_id else '',
            ticket.tecnico.user.username if ticket.tecnico_id else 'Sin asignar',
            ticket.fecha_creacion.strftime('%d/%m/%Y %H:%M') if ticket.fecha_creacion else '',
            ticket.fecha_inicio.strftime('%d/%m/%Y %H:%M') if ticket.fecha_inicio else '',
            ticket.fecha_limite.strftime('%d/%m/%Y %H:%M') if ticket.fecha_limite else '',
            ticket.fecha_conclusion.strftime('%d/%m/%Y %H:%M') if ticket.fecha_conclusion else '',
            ticket.comentario_tecnico or '',
        ])

    workbook_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <sheets>
  <sheet name="Tickets" sheetId="1" r:id="rId1"/>
 </sheets>
</workbook>'''

    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''

    root_rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

    content_types_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="xml" ContentType="application/xml"/>
 <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
 <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>'''

    output = BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types_xml)
        zf.writestr('_rels/.rels', root_rels_xml)
        zf.writestr('xl/workbook.xml', workbook_xml)
        zf.writestr('xl/_rels/workbook.xml.rels', rels_xml)
        zf.writestr('xl/worksheets/sheet1.xml', _sheet_xml(rows))

    return output.getvalue()

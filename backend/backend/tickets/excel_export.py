from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


def _col_name(index):
    name = ''
    while index > 0:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def _sheet_xml(rows):
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

    lines.extend(['</sheetData>', '</worksheet>'])
    return ''.join(lines)


def build_comparison_workbook(base_summary, compare_summary):
    rows = [
        ['Comparativo mensual de tickets'],
        [],
        ['Indicador', base_summary['label'], compare_summary['label'] if compare_summary else 'Sin comparacion'],
        ['Total tickets', base_summary['total_tickets'], compare_summary['total_tickets'] if compare_summary else ''],
        ['Tickets vencidos', base_summary['tickets_vencidos'], compare_summary['tickets_vencidos'] if compare_summary else ''],
        [
            'Tecnico con mas resueltos',
            (base_summary['tecnico_con_mas_incidencias_resueltas'] or {}).get('tecnico__user__username', 'Sin datos'),
            (compare_summary['tecnico_con_mas_incidencias_resueltas'] or {}).get('tecnico__user__username', 'Sin datos')
            if compare_summary else '',
        ],
        [
            'Tecnico con menor carga',
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
            ['Ranking tecnicos comparacion'],
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
        ['Sucursales con mas incidencias base'],
        ['Sucursal', 'Total'],
    ])
    for item in base_summary['sucursales_con_mas_incidencias']:
        rows.append([item.get('sucursal__nombre', ''), item.get('total', 0)])

    if compare_summary:
        rows.extend([
            [],
            ['Sucursales con mas incidencias comparacion'],
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
            'Titulo',
            'Descripcion',
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
            'Comentario tecnico',
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

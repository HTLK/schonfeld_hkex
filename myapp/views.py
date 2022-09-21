from django.shortcuts import render
from django.http import HttpResponse
from .forms import HKEXForm
from .hkex import HKEXInput, HKEXConnection
# Create your views here.
def contact(request):

    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick
    from io import BytesIO
    import base64
    import pandas as pd

    html = ''
    chg_summary_html = ''
    graphic = ''

    if request.method == 'POST':
        form = HKEXForm(request.POST)
        if form.is_valid():
            stock_code = form.cleaned_data['stock_code']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            chg_threshold = float(form.cleaned_data['change_threshold'])

            hkex_input = HKEXInput(stock_code, start_date, end_date, chg_threshold)

            hkex_obj = HKEXConnection(hkex_input)
            hkex_obj.setDate()
            hkex_obj.runAnalysis()

            fig, ax = plt.subplots(figsize=(16, 10))
            hkex_obj.shareholding_data.head(10).plot.bar(title = 'Top 10 Participants by Shareholding',y = 'participant_pct_holding', x = 'participant_name', ax = ax)
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

            plt.tight_layout()

            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()

            graphic = base64.b64encode(image_png)
            graphic = graphic.decode('utf-8')

            hkex_obj.shareholding_data['participant_pct_holding'] = hkex_obj.shareholding_data['participant_pct_holding'].astype(float).map("{:.2%}".format)
            hkex_obj.shareholding_data.columns = ['Participant ID', 'Participant Name', 'Participant Address', 'Shareholding', '% of Total Issue']
            html = hkex_obj.shareholding_data.to_html()

            hkex_obj.runChangeAnalysis()
            if hkex_obj.chg_summary == None:
                hkex_obj.chg_summary = pd.DataFrame(columns = ['Participant ID',
                                                      'Name of CCASS Participant',
                                                      '% Change in total number of Issued Shares/ Warrants/ Units held',
                                                      'Date of Transaction'
                                                      ])
            else:
                hkex_obj.chg_summary['% Change in total number of Issued Shares/ Warrants/ Units held'] = hkex_obj.chg_summary['% Change in total number of Issued Shares/ Warrants/ Units held'].astype(float).map("{:.2%}".format)
            chg_summary_html = hkex_obj.chg_summary.to_html()

    form = HKEXForm()
    return render(request, 'form.html', {'form':form, 'html':html, 'chg_summary': chg_summary_html, 'graphic':graphic})

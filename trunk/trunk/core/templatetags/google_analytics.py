from django import template
from django.conf import settings

register = template.Library()

def simple_minify(src):
    lines = []
    for line in src.splitlines():
        line = line.strip();
        if not line.startswith('//'):
            lines.append(line)
            
    return ''.join(lines)
    
def google_analytics_js():    
    code =  getattr(settings, "GOOGLE_ANALYTICS_CODE", False)
    async = getattr(settings, "GOOGLE_ANALYTICS_ASYNC", False)
    minify = getattr(settings, "GOOGLE_ANALYTICS_MINIFY", True)
    
    if not code:
        return "<!-- Goggle Analytics not included because you haven't set the settings.GOOGLE_ANALYTICS_CODE variable! -->"

    if settings.DEBUG:
        return "<!-- Goggle Analytics not included because you are in Debug mode! -->"

    # todo: don't show if currently logged in user is staff, but don't know how to check request.user.is_staff at this point?
    # if someone tells me where to get the request object from, I'll edit this!

    
    pagetrack_code = """
        //track russian and ukrainian search engines
        engines = [
            ["rambler.ru","words"],
            ["nova.rambler.ru","query"],
            ["mail.ru","q"],
            ["go.mail.ru","q"],
            ["search.otvet.mail.ru","q"],
            ["aport.ru","r"],
            ["metabot.ru","st"],
            ["meta.ua","q"],
            ["bigmir.net","q"],
            ["nigma.ru","s"],
            ["search.ukr.net","search_query"],
            ["start.qip.ru","query"],
            ["gogle.com.ua","q"],
            ["google.com.ua","q"],
            ["images.google.com.ua","q"],
            ["search.winamp.com","query"],
            ["search.icq.com","q"],
            ["m.yandex.ru","query"],
            ["gde.ru","keywords"],
            ["genon.ru","QuestionText"],
            ["blogs.yandex.ru", "text"],
            ["webalta.ru", "q"],
            ["akavita.by", "z"],
            ["meta.ua", "q"],
            ["tut.by", "query"],
            ["all.by", "query"],
            ["i.ua", "q"],
            ["online.ua", "q"],
            ["a.ua", "s"],
            ["ukr.net", "search_query"],
            ["search.com.ua", "q"],
            ["search.ua", "query"],
            ["poisk.ru", "text"],
            ["km.ru", "sq"],
            ["liveinternet.ru", "ask"],
            ["gogo.ru", "q"],
            ["quintura.ru", "request"]
        ];
        for (var i=0; i < engines.length; i++) {
            pageTracker._addOrganic(engines[i][0], engines[i][1]);
        };
        pageTracker._trackPageview();  
    """
    if not async:
        # classic ga code
        gacode = """
        <script type="text/javascript">
            var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
            document.write(String.fromCharCode(60) + "script src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'"+String.fromCharCode(62)+String.fromCharCode(60)+"/script"+String.fromCharCode(62));
        </script>
        <script type="text/javascript">
            try {
            var pageTracker = _gat._getTracker("%(uacct)s");
            %(pagetrack)s
        } catch(err) {}</script>
        """ % { 'uacct': code, 'pagetrack': pagetrack_code}
    else:
        # non-blocking js loading, needs jQuery
        # todo: remove jQuery dependency
        gacode = """
        <script type="text/javascript">
        //non blocking js loading (see http://webo.in/articles/habrahabr/56-non-blocking-javascript/)
        function loadScript(name) {
            var js = document.createElement('script');
            js.src = name;
            var head = document.getElementsByTagName('head')[0];
            head.appendChild(js);
        }
        
        function trackGA(code, tryN) {
            if (typeof(_gat) == "undefined") {
                if (tryN <= 100) {
                    setTimeout(function() {trackGA(code, tryN + 1);}, 50);
                }
            } else {
                var pageTracker = _gat._getTracker(code);                
                %(pagetrack)s
            }    
        }
        
        $(document).ready(function() {
            var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");    
            loadScript(gaJsHost + 'google-analytics.com/ga.js');
            trackGA("%(uacct)s", 0);
        });
        </script>
        """  % { 'uacct': code, 'pagetrack': pagetrack_code }
    if minify:
        gacode = simple_minify(gacode)
    return gacode
register.simple_tag(google_analytics_js)
/*jQuery MegaMenu Plugin
 Author: Devadatta Sahoo
 Author URI: http://www.geektantra.com */
var isIE6 = navigator.userAgent.toLowerCase().indexOf('msie 6') != -1;
(function($){
    $.fn.extend({
        isChildOf: function(filter_string){
            var parents = $(this).parents().get();
            for (j = 0; j < parents.length; j++) {
                if ($(parents[j]).is(filter_string)) 
                    return true;
            }
            return false;
        }
    });
})(jQuery);

jQuery.fn.megamenu = function(ContentClass, Options){
    var MenuClass = $(this).attr("class").split(" ")[0];
    var ParentNodeNumber = 0;
    Options = jQuery.extend({
        width: "auto",
        justify: "left"
    }, Options);
    $(ContentClass).after('  <div id="MegaMenuContentShadow" style="display: none;"></div><div id="MegaMenuContent" style="display: none;"></div>');
    $(this).mouseover(function(){
        var MenuContent = $(this).next(ContentClass).html();
        ParentNodeNumber = $('.' + MenuClass).index(this);
        MegaMenuMouseOver(ParentNodeNumber, MenuContent, "click", MenuClass, ContentClass, Options);
        //setTimeout('MegaMenuMouseOver('+ParentNodeNumber+',"'+escape(MenuContent)+'","hover",\''+MenuClass+'\',\''+ContentClass+'\',\''+Options+'\')', 300);
    });
    $(this).click(function(){
        var MenuContent = $(this).next('.MegaMenuContent').html();
        ParentNodeNumber = $('.' + MenuClass).index(this);
        MegaMenuMouseOver(ParentNodeNumber, MenuContent, "click", MenuClass, ContentClass, Options);
    });
    $(this).mouseout(function(){
        MegaMenuMouseOut(ParentNodeNumber, MenuClass, ContentClass);
    });
    $(document).bind('click', function(e){
        var $clicked = $(e.target);
        if ($clicked.isChildOf('#MegaMenuContent') || $clicked.is('#MegaMenuContent') || $clicked.is('.' + MenuClass)) {
        }
        else 
            MegaMenuMouseOut(ParentNodeNumber, MenuClass, ContentClass);
    });
};

function MegaMenuMouseOver(ParentNodeNumber, MenuContent, state, MenuLinkClass, MenuContentClass, Options){
    var MenuLinkClass = (typeof(MenuLinkClass) == 'undefined') ? ".MegaMenuLink" : MenuLinkClass;
    var MenuContentClass = (typeof(MenuContentClass) == 'undefined') ? ".MegaMenuContent" : MenuContentClass;
    
    //var Options = eval('(' + Options + ')');
    if (state == "hover") 
        $('.' + MenuLinkClass).removeClass(MenuLinkClass + 'Active');
    $('.' + MenuLinkClass).eq(ParentNodeNumber).addClass(MenuLinkClass + 'Active');
    
    var selfNode = new Array();
    selfNode['width'] = $('.' + MenuLinkClass).eq(ParentNodeNumber).width();
    selfNode['padding-left'] = parseInt($('.' + MenuLinkClass).eq(ParentNodeNumber).css('padding-left').replace(/px/g, ''));
    selfNode['padding-right'] = parseInt($('.' + MenuLinkClass).eq(ParentNodeNumber).css('padding-right').replace(/px/g, ''));
    selfNode['border-left-width'] = parseInt($('.' + MenuLinkClass).eq(ParentNodeNumber).css('border-left-width').replace(/px/g, ''));
    selfNode['border-right-width'] = parseInt($('.' + MenuLinkClass).eq(ParentNodeNumber).css('border-right-width').replace(/px/g, ''));
    if (isIE6) 
        selfNode['width'] = selfNode['width'] + 10;
    
    if (Options['justify'] == "left") {
        var LeftPos = $('.' + MenuLinkClass).eq(ParentNodeNumber).parent().position().left;
        if (Options['width'] == 'auto') 
            LeftPos = $('.' + MenuLinkClass).eq(ParentNodeNumber).position().left - 10;
    }
    else {
        var RightPos = $('.' + MenuLinkClass).eq(ParentNodeNumber).parent().position().left;
        if (Options['width'] == 'auto') 
            RightPos = $(document).width() - 10 - $('.' + MenuLinkClass).eq(ParentNodeNumber).position().left - selfNode['width'] - selfNode['padding-left'] - selfNode['padding-right'] - selfNode['border-left-width'] - selfNode['border-right-width'];
    }
    
    var TopPos = $('.' + MenuLinkClass).eq(ParentNodeNumber).height() + $('.' + MenuLinkClass).eq(ParentNodeNumber).position().top + parseInt($('.' + MenuLinkClass).eq(ParentNodeNumber).css("padding-top").replace(/px/g, '')) + parseInt($('.' + MenuLinkClass).eq(ParentNodeNumber).css("padding-bottom").replace(/px/g, '')) + parseInt($('.' + MenuLinkClass).eq(ParentNodeNumber).css("border-top-width").replace(/px/g, ''));
    
    MenuContent = unescape(MenuContent);
    
    if (LeftPos) {
        $("#MegaMenuContent").css('left', LeftPos + 'px');
        $("#MegaMenuContentShadow").css('left', (LeftPos) + 'px');
    }
    else {
        $("#MegaMenuContent").css('right', RightPos + 'px');
        $("#MegaMenuContentShadow").css('right', (RightPos - 4) + 'px');
    }
    $("#MegaMenuContent").css('top', TopPos + 'px');
    $("#MegaMenuContentShadow").css('top', TopPos + 'px');
    if (Options['width']) {
        $("#MegaMenuContent").css('width', Options['width']);
        $("#MegaMenuContentShadow").css('width', Options['width']);
    }
    $("#MegaMenuContent").html('' + MenuContent);
    $("#MegaMenuContent").slideDown("fast");
    $("#MegaMenuContentShadow").html('' + MenuContent);
    $("#MegaMenuContentShadow").slideDown("fast");
    
    $("#MegaMenuContent,#MegaMenuContentShadow").mouseover(function(){
        $('#MegaMenuContent').show();
        $('#MegaMenuContentShadow').show();
        
        $('.' + MenuLinkClass).removeClass(MenuLinkClass + 'Active');
        $('.' + MenuLinkClass).eq(ParentNodeNumber).addClass(MenuLinkClass + 'Active');
    });
    $("#MegaMenuContent,#MegaMenuContentShadow").mouseout(function(){
        $("#MegaMenuContent").hide()
        $("#MegaMenuContentShadow").hide()
        $('.' + MenuLinkClass).removeClass(MenuLinkClass + 'Active');
    });
}

function MegaMenuMouseOut(ParentNodeNumber, MenuLinkClass, MenuContentClass){
    $('#MegaMenuContent').hide();
    $('#MegaMenuContentShadow').hide();
    var MenuLinkClass = (typeof(MenuLinkClass) == 'undefined') ? ".MegaMenuLink" : MenuLinkClass;
    $('.' + MenuLinkClass).eq(ParentNodeNumber).removeClass(MenuLinkClass + 'Active');
}

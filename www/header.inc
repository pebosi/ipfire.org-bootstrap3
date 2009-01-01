<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="de" lang="de">
	<head>
		<meta http-equiv="content-type" content="text/html; charset=utf-8" />
		<title>%(title)s</title>
		<meta name="keywords" content="Linux, Firewall, IPCop, IPFire, Security" />
		<meta name="description" content="" />
		<meta name="verify-v1" content="2LEf3W8naILGWVy2dhedSVEHPXTpp2xFNVsHXZMH1JI=" />
		<link rel="stylesheet" type="text/css" href="../style.css" />
		<link rel="alternate" type="application/rss+xml" title="RSS" href="http://www.ipfire.org/data/feeds/main-en.rss" />
	<!--[if lt IE 7]>
		<script type="text/javascript">
			function correctPNG() // correctly handle PNG transparency in Win IE 5.5 or higher.
			{
				for(var i=0; i<document.images.length; i++)
				{
					var img = document.images[i]
					var imgName = img.src.toUpperCase()
					if (imgName.substring(imgName.length-3, imgName.length) == "PNG")
					{
						var imgID = (img.id) ? "id='" + img.id + "' " : ""
						var imgClass = (img.className) ? "class='" + img.className + "' " : ""
						var imgTitle = (img.title) ? "title='" + img.title + "' " : "title='" + img.alt + "' "
						var imgStyle = "display:inline-block;" + img.style.cssText
						if (img.align == "left") imgStyle = "float:left;" + imgStyle
						if (img.align == "right") imgStyle = "float:right;" + imgStyle
						if (img.parentElement.href) imgStyle = "cursor:hand;" + imgStyle
						var strNewHTML = "<span " + imgID + imgClass + imgTitle
							+ " style=\"" + "width:" + img.width + "px; height:" + img.height + "px;" + imgStyle + ";"
							+ "filter:progid:DXImageTransform.Microsoft.AlphaImageLoader"
							+ "(src=\'" + img.src + "\', sizingMethod='scale');\"></span>"
						img.outerHTML = strNewHTML
						i = i-1
					}
				}
			}
			window.attachEvent("onload", correctPNG);
		</script>
	<![endif]-->
	</head>
	<body>
		<div id="header">
			<div id="header_inner" class="fixed">
				<div id="logo">
					<img src="/images/icons/ipfire.png" width="48px" height="48px" class="symbol" alt="IPFire" />
					<h1><span>IPFire</span>.org</h1>
					<br />
					<h2>Security today!</h2>
				</div>
				<div id="lang">
					<a href="/%(document_name)s/en" ><img src="/images/en.gif" alt="english" /></a>
					<a href="/%(document_name)s/de" ><img src="/images/de.gif" alt="german" /></a>
				</div>
				%(menu)s
			</div>
		</div>
		<div id="main">
			<div id="main_inner" class="fixed">
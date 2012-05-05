import re
from operator import attrgetter
from lxml.etree import tounicode
from lxml.etree import tostring
from lxml.html import fragment_fromstring
from lxml.html import fromstring
from breadability.document import OriginalDocument
from breadability.utils import cached_property

# A series of sets of attributes we check to help in determining if a node is
# a potential candidate or not.
CLS_UNLIKELY = set([
    'combx', 'comment', 'community', 'disqus', 'extra', 'foot', 'header',
    'menu', '' 'remark', 'rss', 'shoutbox', 'sidebar', 'sponsor', 'ad-break',
    'agegate', 'pagination' '', 'pager', 'popup', 'tweet', 'twitter',
])
CLS_MAYBE = set([
    'and', 'article', 'body', 'column', 'main', 'shadow',
])
CLS_WEIGHT_POSITIVE = set(['article', 'body', 'content', 'entry', 'hentry',
    'main', 'page', 'pagination', 'post', 'text', 'blog', 'story'])
CLS_WEIGHT_NEGATIVE = set(['combx', 'comment', 'com-', 'contact', 'foot',
    'footer', 'footnote', 'masthead', 'media', 'meta', 'outbrain', 'promo',
    'related', 'scroll', 'shoutbox', 'sidebar', 'sponsor', 'shopping', 'tags',
    'tool', 'widget'])


def check_node_attr(node, attr, checkset):
    attr = node.get(attr) or ""
    check = set(attr.lower().split(' '))
    if check.intersection(checkset):
        return True
    else:
        return False


def drop_tag(doc, *tags):
    """Helper to just remove any nodes that match this html tag passed in

    :param *tags: one or more html tag strings to remove e.g. style, script

    """
    [[n.drop_tree() for n in doc.iterfind(".//" + tag)]
            for tag in tags]
    return doc


def build_base_document(html):
    """Return a base document with the body as root.

    :param html: Parsed Element object

    """
    if html.tag == 'body':
        html.tag = 'div'
        found_body = html
    else:
        found_body = html.find('.//body')

    if found_body is None:
        fragment = fragment_fromstring('<div/>')
        fragment.set('id', 'readabilityBody')
        fragment.append(html)
        return fragment
    else:
        found_body.tag = 'div'
        found_body.set('id', 'readabilityBody')

    return found_body


def get_link_density(node):
    """Generate a value for the number of links in the node.

    :param node: pared elementree node
    :returns float:

    """
    link_length = len("".join([a.text or "" for a in node.findall(".//a")]))
    text_length = len(node.text_content())
    return float(link_length) / max(text_length, 1)


def transform_misused_divs_into_paragraphs(doc):
    """Turn all divs that don't have children block level elements into p's

    Since we can't change the tree as we iterate over it, we must do this
    before we process our document.

    The idea is that we process all divs and if the div does not contain
    another list of divs, then we replace it with a p tag instead appending
    it's contents/children to it.

    """
    for elem in doc.iter(tag='div'):
        child_tags = [n.tag for n in elem.getchildren()]
        if 'div' not in child_tags:
            # if there is no div inside of this div...then it's a leaf
            # node in a sense.
            # We need to create a <p> and put all it's contents in there
            # We'll just stringify it, then regex replace the first/last
            # div bits to turn them into <p> vs <div>.
            orig = tounicode(elem).strip()
            started = re.sub(r'^<\s*div', '<p', orig)
            ended = re.sub(r'div>$', 'p>', started)
            elem.getparent().replace(elem, fromstring(ended))

    return doc


def check_siblings(candidate_node, candidate_list):
    """Look through siblings for content that might also be related.

    Things like preambles, content split by ads that we removed, etc.

    """
    candidate_css = candidate_node.node.get('class')
    potential_target = candidate_node.content_score * 0.2
    sibling_target_score = potential_target if potential_target > 10 else 10
    parent = candidate_node.node.getparent()
    siblings = parent.getchildren() if parent is not None else []

    for sibling in siblings:
        append = False
        content_bonus = 0;

        if sibling is candidate_node.node:
            append = True

        # Give a bonus if sibling nodes and top candidates have the example
        # same classname
        if candidate_css and sibling.get('class') == candidate_css:
            content_bonus += candidate_node.content_score * 0.2;

        if sibling in candidate_list:
            adjusted_score = candidate_list[sibling].content_score + \
                content_bonus

            if adjusted_score >= sibling_target_score:
                append = True

        if sibling.tag == 'p':
            link_density = get_link_density(sibling)
            content = sibling.text_content()
            content_length  = len(content)

            if content_length > 80 and link_density < 0.25:
                append = true;
            elif content_length < 80 and link_density == 0:
                if ". " in content:
                    append = True

        if append:
            if sibling.tag not in ['div', 'p']:
                # We have a node that isn't a common block level element, like
                # a form or td tag. Turn it into a div so it doesn't get
                # filtered out later by accident.
                sibling.tag = 'div'

            candidate_node.node.append(sibling)

    return candidate_node


###### SCORING


def get_class_weight(node):
    """Get an elements class/id weight.

    We're using sets to help efficiently check for existence of matches.

    """
    weight = 0
    if check_node_attr(node, 'class', CLS_WEIGHT_NEGATIVE):
        weight = weight - 25
    if check_node_attr(node, 'class', CLS_WEIGHT_POSITIVE):
        weight = weight + 25

    if check_node_attr(node, 'id', CLS_WEIGHT_NEGATIVE):
        weight = weight - 25
    if check_node_attr(node, 'id', CLS_WEIGHT_POSITIVE):
        weight = weight + 25

    return weight


def score_candidates(nodes):
    """Given a list of potential nodes, find some initial scores to start"""
    MIN_HIT_LENTH = 25
    candidates = {}

    for node in nodes:
        content_score = 0
        parent = node.getparent()
        grand = parent.getparent() if parent is not None else None
        innertext = node.text

        if parent is None or grand is None:
            continue

        # If this paragraph is less than 25 characters, don't even count it.
        if innertext and len(innertext) < MIN_HIT_LENTH:
            continue

        # Initialize readability data for the parent.
        # if the parent node isn't in the candidate list, add it
        if parent not in candidates:
            candidates[parent] = CandidateNode(parent)

        if grand not in candidates:
            candidates[grand] = CandidateNode(grand)

        # Add a point for the paragraph itself as a base.
        content_score += 1

        # Add points for any commas within this paragraph
        content_score += innertext.count(',') if innertext else 0

        # For every 100 characters in this paragraph, add another point. Up to
        # 3 points.
        length_points = len(innertext) % 100 if innertext else 0
        content_score = length_points if length_points > 3 else 3

        # Add the score to the parent. The grandparent gets half. */
        if parent is not None:
            candidates[parent].content_score += content_score
        if grand is not None:
            candidates[grand].content_score += content_score

        for candidate in candidates.values():
            candidate.content_score = candidate.content_score * (1 -
                    get_link_density(candidate.node))

    return candidates


def process(doc):
    """Process this doc to make it readable.

    Here's we're going to remove unlikely nodes, find scores on the rest, and
    clean up and return the final best match.

    """
    unlikely = []
    scorable_node_tags = ['p', 'td', 'pre']
    nodes_to_score = []

    def is_unlikely_node(node):
        """Short helper for checking unlikely status.

        If the class or id are in the unlikely list, and there's not also a
        class/id in the likely list then it might need to be removed.

        """
        unlikely = check_node_attr(node, 'class', CLS_UNLIKELY) or \
            check_node_attr(node, 'id', CLS_UNLIKELY)

        maybe = check_node_attr(node, 'class', CLS_MAYBE) or \
            check_node_attr(node, 'id', CLS_MAYBE)

        if unlikely and not maybe and node.tag != 'body':
            return True
        else:
            return False

    for node in doc.getiterator():
        if is_unlikely_node(node):
            unlikely.append(node)

        if node.tag in scorable_node_tags:
            nodes_to_score.append(node)

    # process our clean up instructions
    [n.drop_tree() for n in unlikely]

    candidates = score_candidates(nodes_to_score)
    return candidates


class CandidateNode(object):
    """We need Candidate nodes we use to track possible article matches

    We might have a bunch of these so we use __slots__ to keep memory usage
    down.

    """
    __slots__ = ['node', 'content_score']

    def __init__(self, node):
        """Given node, set an initial score and weigh based on css and id"""
        self.node = node
        content_score = 0
        if node.tag == 'div':
            content_score = 5

        if node.tag in ['pre', 'td', 'blockquote']:
            content_score = 3

        if node.tag in ['address', 'ol', 'ul', 'dl', 'dd', 'dt', 'li',
            'form']:
            content_score = -3
        if node.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'th']:
            content_score = -5
        content_score += get_class_weight(node)
        self.content_score = content_score


class Article(object):
    """Parsed readable object"""

    def __init__(self, html, url=None):
        self.orig = OriginalDocument(html, url=url)

    def __str__(self):
        return tostring(self.readable)

    def __unicode__(self):
        return tounicode(self.readable)

    @cached_property(ttl=600)
    def readable(self):
        """The readable parsed article"""
        doc = self.orig.html
        doc = drop_tag(doc, 'script', 'link', 'style', 'noscript')
        doc = transform_misused_divs_into_paragraphs(doc)
        candidates = process(doc)

        if candidates:
            # right now we return the highest scoring candidate content
            by_score = sorted([c for c in candidates.values()],
                key=attrgetter('content_score'), reverse=True)

            # since we have several candidates, check the winner's siblings
            # for extra content
            winner = by_score[0]
            updated_winner = check_siblings(winner, candidates)
            doc = build_base_document(updated_winner.node)
        else:
            doc = build_base_document(doc)

        return doc


"""
Algorithm notes for


    /***
     * grabArticle - Using a variety of metrics (content score, classname, element types), find the content that is
     *               most likely to be the stuff a user wants to read. Then return it wrapped up in a div.
     *
     * @param page a document to run upon. Needs to be a full document, complete with body.
     * @return Element
    **/
    grabArticle: function (page) {
        var stripUnlikelyCandidates = readability.flagIsActive(readability.FLAG_STRIP_UNLIKELYS),
            isPaging = (page !== null) ? true: false;

        page = page ? page : document.body;

        var pageCacheHtml = page.innerHTML;

        var allElements = page.getElementsByTagName('*');

        /**
         * First, node prepping. Trash nodes that look cruddy (like ones with the class name "comment", etc), and turn divs
         * into P tags where they have been used inappropriately (as in, where they contain no other block level elements.)
         *
         * Note: Assignment from index for performance. See http://www.peachpit.com/articles/article.aspx?p=31567&seqNum=5
         * TODO: Shouldn't this be a reverse traversal?
        **/
        var node = null;
        var nodesToScore = [];
        for(var nodeIndex = 0; (node = allElements[nodeIndex]); nodeIndex+=1) {
            /* Remove unlikely candidates */
            if (stripUnlikelyCandidates) {
                var unlikelyMatchString = node.className + node.id;
                if (
                    (
                        unlikelyMatchString.search(readability.regexps.unlikelyCandidates) !== -1 &&
                        unlikelyMatchString.search(readability.regexps.okMaybeItsACandidate) === -1 &&
                        node.tagName !== "BODY"
                    )
                )
                {
                    dbg("Removing unlikely candidate - " + unlikelyMatchString);
                    node.parentNode.removeChild(node);
                    nodeIndex-=1;
                    continue;
                }
            }

            if (node.tagName === "P" || node.tagName === "TD" || node.tagName === "PRE") {
                nodesToScore[nodesToScore.length] = node;
            }

            /* Turn all divs that don't have children block level elements into p's */
            if (node.tagName === "DIV") {
                if (node.innerHTML.search(readability.regexps.divToPElements) === -1) {
                    var newNode = document.createElement('p');
                    try {
                        newNode.innerHTML = node.innerHTML;
                        node.parentNode.replaceChild(newNode, node);
                        nodeIndex-=1;

                        nodesToScore[nodesToScore.length] = node;
                    }
                    catch(e) {
                        dbg("Could not alter div to p, probably an IE restriction, reverting back to div.: " + e);
                    }
                }
                else
                {
                    /* EXPERIMENTAL */
                    for(var i = 0, il = node.childNodes.length; i < il; i+=1) {
                        var childNode = node.childNodes[i];
                        if(childNode.nodeType === 3) { // Node.TEXT_NODE
                            var p = document.createElement('p');
                            p.innerHTML = childNode.nodeValue;
                            p.style.display = 'inline';
                            p.className = 'readability-styled';
                            childNode.parentNode.replaceChild(p, childNode);
                        }
                    }
                }
            }
        }

        /**
         * Loop through all paragraphs, and assign a score to them based on how content-y they look.
         * Then add their score to their parent node.
         *
         * A score is determined by things like number of commas, class names, etc. Maybe eventually link density.
        **/
        var candidates = [];
        for (var pt=0; pt < nodesToScore.length; pt+=1) {
            var parentNode      = nodesToScore[pt].parentNode;
            var grandParentNode = parentNode ? parentNode.parentNode : null;
            var innerText       = readability.getInnerText(nodesToScore[pt]);

            if(!parentNode || typeof(parentNode.tagName) === 'undefined') {
                continue;
            }

            /* If this paragraph is less than 25 characters, don't even count it. */
            if(innerText.length < 25) {
                continue; }

            /* Initialize readability data for the parent. */
            if(typeof parentNode.readability === 'undefined') {
                readability.initializeNode(parentNode);
                candidates.push(parentNode);
            }

            /* Initialize readability data for the grandparent. */
            if(grandParentNode && typeof(grandParentNode.readability) === 'undefined' && typeof(grandParentNode.tagName) !== 'undefined') {
                readability.initializeNode(grandParentNode);
                candidates.push(grandParentNode);
            }

            var contentScore = 0;

            /* Add a point for the paragraph itself as a base. */
            contentScore+=1;

            /* Add points for any commas within this paragraph */
            contentScore += innerText.split(',').length;

            /* For every 100 characters in this paragraph, add another point. Up to 3 points. */
            contentScore += Math.min(Math.floor(innerText.length / 100), 3);

            /* Add the score to the parent. The grandparent gets half. */
            parentNode.readability.contentScore += contentScore;

            if(grandParentNode) {
                grandParentNode.readability.contentScore += contentScore/2;
            }
        }

        /**
         * After we've calculated scores, loop through all of the possible candidate nodes we found
         * and find the one with the highest score.
        **/
        var topCandidate = null;
        for(var c=0, cl=candidates.length; c < cl; c+=1)
        {
            /**
             * Scale the final candidates score based on link density. Good content should have a
             * relatively small link density (5% or less) and be mostly unaffected by this operation.
            **/
            candidates[c].readability.contentScore = candidates[c].readability.contentScore * (1-readability.getLinkDensity(candidates[c]));

            dbg('Candidate: ' + candidates[c] + " (" + candidates[c].className + ":" + candidates[c].id + ") with score " + candidates[c].readability.contentScore);

            if(!topCandidate || candidates[c].readability.contentScore > topCandidate.readability.contentScore) {
                topCandidate = candidates[c]; }
        }

        /**
         * If we still have no top candidate, just use the body as a last resort.
         * We also have to copy the body node so it is something we can modify.
         **/
        if (topCandidate === null || topCandidate.tagName === "BODY")
        {
            topCandidate = document.createElement("DIV");
            topCandidate.innerHTML = page.innerHTML;
            page.innerHTML = "";
            page.appendChild(topCandidate);
            readability.initializeNode(topCandidate);
        }

        /**
         * Now that we have the top candidate, look through its siblings for content that might also be related.
         * Things like preambles, content split by ads that we removed, etc.
        **/
        var articleContent        = document.createElement("DIV");
        if (isPaging) {
            articleContent.id     = "readability-content";
        }
        var siblingScoreThreshold = Math.max(10, topCandidate.readability.contentScore * 0.2);
        var siblingNodes          = topCandidate.parentNode.childNodes;


        for(var s=0, sl=siblingNodes.length; s < sl; s+=1) {
            var siblingNode = siblingNodes[s];
            var append      = false;

            /**
             * Fix for odd IE7 Crash where siblingNode does not exist even though this should be a live nodeList.
             * Example of error visible here: http://www.esquire.com/features/honesty0707
            **/
            if(!siblingNode) {
                continue;
            }

            dbg("Looking at sibling node: " + siblingNode + " (" + siblingNode.className + ":" + siblingNode.id + ")" + ((typeof siblingNode.readability !== 'undefined') ? (" with score " + siblingNode.readability.contentScore) : ''));
            dbg("Sibling has score " + (siblingNode.readability ? siblingNode.readability.contentScore : 'Unknown'));

            if(siblingNode === topCandidate)
            {
                append = true;
            }

            var contentBonus = 0;
            /* Give a bonus if sibling nodes and top candidates have the example same classname */
            if(siblingNode.className === topCandidate.className && topCandidate.className !== "") {
                contentBonus += topCandidate.readability.contentScore * 0.2;
            }

            if(typeof siblingNode.readability !== 'undefined' && (siblingNode.readability.contentScore+contentBonus) >= siblingScoreThreshold)
            {
                append = true;
            }

            if(siblingNode.nodeName === "P") {
                var linkDensity = readability.getLinkDensity(siblingNode);
                var nodeContent = readability.getInnerText(siblingNode);
                var nodeLength  = nodeContent.length;

                if(nodeLength > 80 && linkDensity < 0.25)
                {
                    append = true;
                }
                else if(nodeLength < 80 && linkDensity === 0 && nodeContent.search(/\.( |$)/) !== -1)
                {
                    append = true;
                }
            }

            if(append) {
                dbg("Appending node: " + siblingNode);

                var nodeToAppend = null;
                if(siblingNode.nodeName !== "DIV" && siblingNode.nodeName !== "P") {
                    /* We have a node that isn't a common block level element, like a form or td tag. Turn it into a div so it doesn't get filtered out later by accident. */

                    dbg("Altering siblingNode of " + siblingNode.nodeName + ' to div.');
                    nodeToAppend = document.createElement("DIV");
                    try {
                        nodeToAppend.id = siblingNode.id;
                        nodeToAppend.innerHTML = siblingNode.innerHTML;
                    }
                    catch(er) {
                        dbg("Could not alter siblingNode to div, probably an IE restriction, reverting back to original.");
                        nodeToAppend = siblingNode;
                        s-=1;
                        sl-=1;
                    }
                } else {
                    nodeToAppend = siblingNode;
                    s-=1;
                    sl-=1;
                }

                /* To ensure a node does not interfere with readability styles, remove its classnames */
                nodeToAppend.className = "";

                /* Append sibling and subtract from our list because it removes the node when you append to another node */
                articleContent.appendChild(nodeToAppend);
            }
        }

        /**
         * So we have all of the content that we need. Now we clean it up for presentation.
        **/
        readability.prepArticle(articleContent);

        if (readability.curPageNum === 1) {
            articleContent.innerHTML = '<div id="readability-page-1" class="page">' + articleContent.innerHTML + '</div>';
        }

        /**
         * Now that we've gone through the full algorithm, check to see if we got any meaningful content.
         * If we didn't, we may need to re-run grabArticle with different flags set. This gives us a higher
         * likelihood of finding the content, and the sieve approach gives us a higher likelihood of
         * finding the -right- content.
        **/
        if(readability.getInnerText(articleContent, false).length < 250) {
        page.innerHTML = pageCacheHtml;

            if (readability.flagIsActive(readability.FLAG_STRIP_UNLIKELYS)) {
                readability.removeFlag(readability.FLAG_STRIP_UNLIKELYS);
                return readability.grabArticle(page);
            }
            else if (readability.flagIsActive(readability.FLAG_WEIGHT_CLASSES)) {
                readability.removeFlag(readability.FLAG_WEIGHT_CLASSES);
                return readability.grabArticle(page);
            }
            else if (readability.flagIsActive(readability.FLAG_CLEAN_CONDITIONALLY)) {
                readability.removeFlag(readability.FLAG_CLEAN_CONDITIONALLY);
                return readability.grabArticle(page);
            } else {
                return null;
            }
        }

        return articleContent;
    },

    /**
"""

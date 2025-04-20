from typing import Dict, List, Any
from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class SentimentConfig(BaseModel):
    """Configuration for sentiment analysis."""
    type: str = 'vader'  # 'basic', 'vader', ou 'bert'
    language: str = 'en'  # 'en' ou 'pt'

class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""
    
    # RSS feed settings
    rss_feeds: List[str] = Field(
        default=[
            "https://www.technologyreview.com/topic/artificial-intelligence/feed",
            "https://deepmind.com/blog/feed/basic/",
            "https://machinelearningmastery.com/blog/feed/",
            "https://bair.berkeley.edu/blog/feed.xml",
            "https://machinelearningmastery.com/blog/feed/",
            "https://bair.berkeley.edu/blog/feed.xml",
            "http://news.mit.edu/rss/topic/artificial-intelligence2",
            "https://deepmind.com/blog/feed/basic/",
            "https://www.unite.ai/feed/",
            "https://ai2people.com/feed/",
            "https://hanhdbrown.com/feed/",
            "https://dailyai.com/feed/",
            "https://nyheter.aitool.se/feed/",
            "https://www.spritle.com/blog/feed/",
            "https://yatter.in/feed/",
            "https://www.shaip.com/feed/",
            "https://www.greataiprompts.com/feed/",
            "https://zerothprinciples.substack.com/feed",
            "https://airevolution.blog/feed/",
            "https://saal.ai/feed/",
            "https://aicorr.com/feed/",
            "https://qudata.com/en/news/rss.xml",
            "https://hanhdbrown.com/category/ai/feed/",
            "https://www.oreilly.com/radar/topics/ai-ml/feed/index.xml",
            "https://blogs.sas.com/content/topic/artificial-intelligence/feed/",
            "https://blogs.rstudio.com/ai/index.xml",
            "https://www.technologyreview.com/topic/artificial-intelligence/feed",
            "http://www.kdnuggets.com/feed",
            "https://research.aimultiple.com/feed/",
            "https://nanonets.com/blog/rss/",
            "https://www.datarobot.com/blog/feed/",
            "https://becominghuman.ai/feed",
            "https://bigdataanalyticsnews.com/category/artificial-intelligence/feed/",
            "https://blog.kore.ai/rss.xml",
            "https://www.clarifai.com/blog/rss.xml",
            "https://expertsystem.com/feed/",
            "https://theaisummer.com/feed.xml",
            "https://www.aiiottalk.com/feed/",
            "https://www.isentia.com/feed/",
            "https://chatbotslife.com/feed",
            "http://www.marketingaiinstitute.com/blog/rss.xml",
            "https://www.topbots.com/feed/",
            "https://www.artificiallawyer.com/feed/",
            "https://dlabs.ai/feed/",
            "https://www.aitimejournal.com/feed/",
            "https://insights.fusemachines.com/feed/",
            "https://intelligence.org/blog/feed/",
            "https://deepcognition.ai/feed/",
            "https://1reddrop.com/feed/",
            "https://www.viact.ai/blog-feed.xml",
            "https://robotwritersai.com/feed/",
            "https://aihub.org/feed/?cat=-473",
            "https://usmsystems.com/blog/feed/",
            "https://www.aiplusinfo.com/feed/",
            "https://metadevo.com/feed/",
            "https://www.cogitotech.com/feed/",
            "https://datamachina.substack.com/feed",
            "https://vue.ai/blog/feed/",
            "https://www.greatlearning.in/blog/category/artificial-intelligence/feed/",
            "https://topmarketingai.com/feed/",
            "https://appzoon.com/feed/",
            "https://medium.com/feed/@securechainai",
            "https://blogs.microsoft.com/ai/feed/",
            "https://chatbotsmagazine.com/feed",
            "https://findnewai.com/feed/",
            "http://kavita-ganesan.com/feed",
            "https://pandio.com/feed/",
            "https://www.danrose.ai/blog?format=rss",
            "https://www.edia.nl/edia-blog?format=rss",
            "http://www.eledia.org/e-air/feed/",
            "http://ankit-ai.blogspot.com/feeds/posts/default?alt=rss",
            "https://editorialia.com/feed/",
            "http://blog.datumbox.com/feed/",
            "https://daleonai.com/feed.xml",
            "https://binaryinformatics.com/category/ai/feed/",
            "https://www.kochartech.com/feed/",
            "https://medium.com/feed/@Francesco_AI",
            "https://medium.com/feed/archieai",
            "https://medium.com/feed/ai-roadmap-institute",
            "https://docs.microsoft.com/en-us/archive/blogs/machinelearning/feed.xml",
            "https://www.404media.co/rss",
            "https://magazine.sebastianraschka.com/feed",
            "https://aiacceleratorinstitute.com/rss/",
            "https://ai-techpark.com/category/ai/feed/",
            "https://knowtechie.com/category/ai/feed/",
            "https://aimodels.substack.com/feed",
            "https://www.artificialintelligence-news.com/feed/rss/",
            "https://venturebeat.com/category/ai/feed/",
            "https://ainowinstitute.org/category/news/feed",
            "https://siliconangle.com/category/ai/feed",
            "https://aisnakeoil.substack.com/feed",
            "https://www.anaconda.com/blog/feed",
            "https://analyticsindiamag.com/feed/",
            "https://feeds.arstechnica.com/arstechnica/index",
            "https://www.theguardian.com/technology/artificialintelligenceai/rss",
            "https://spacenews.com/tag/artificial-intelligence/feed/",
            "https://futurism.com/categories/ai-artificial-intelligence/feed",
            "https://www.wired.com/feed/tag/ai/latest/rss",
            "https://www.techrepublic.com/rssfeeds/topic/artificial-intelligence/",
            "https://medium.com/feed/artificialis",
            "https://siliconangle.com/category/big-data/feed",
            "https://davidstutz.de/category/blog/feed",
            "https://neptune.ai/blog/feed",
            "https://blog.eleuther.ai/index.xml",
            "https://pyimagesearch.com/blog/feed",
            "https://feeds.bloomberg.com/technology/news.rss",
            "https://www.wired.com/feed/category/business/latest/rss",
            "https://every.to/chain-of-thought/feed.xml",
            "https://huyenchip.com/feed",
            "https://news.crunchbase.com/feed",
            "https://arxiv.org/rss/cs.CL",
            "https://arxiv.org/rss/cs.CV",
            "https://arxiv.org/rss/cs.LG",
            "https://dagshub.com/blog/rss/",
            "https://www.databricks.com/feed",
            "https://datafloq.com/feed/?post_type=post",
            "https://www.datanami.com/feed/",
            "https://debuggercafe.com/feed/",
            "https://deephaven.io/blog/rss.xml",
            "https://tech.eu/category/deep-tech/feed",
            "https://departmentofproduct.substack.com/feed",
            "https://www.eetimes.com/feed",
            "https://www.engadget.com/rss.xml",
            "https://eugeneyan.com/rss/",
            "https://explosion.ai/feed",
            "https://www.freethink.com/feed/all",
            "https://www.generational.pub/feed",
            "https://www.forrester.com/blogs/category/artificial-intelligence-ai/feed",
            "https://www.ghacks.net/feed/",
            "https://gizmodo.com/rss",
            "https://globalnews.ca/tag/artificial-intelligence/feed",
            "https://gradientflow.com/feed/",
            "https://hackernoon.com/tagged/ai/feed",
            "https://feeds.feedburner.com/HealthTechMagazine",
            "https://huggingface.co/blog/feed.xml",
            "https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss",
            "https://feed.infoq.com/ai-ml-data-eng/",
            "https://insidebigdata.com/feed",
            "https://www.interconnects.ai/feed",
            "https://www.ibtimes.com/rss",
            "https://www.jmlr.org/jmlr.xml",
            "https://www.kdnuggets.com/feed",
            "https://blog.langchain.dev/rss/",
            "https://lastweekin.ai/feed",
            "https://www.latent.space/feed",
            "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
            "https://lightning.ai/pages/feed/",
            "https://blog.ml.cmu.edu/feed",
            "https://www.nature.com/subjects/machine-learning.rss",
            "https://www.marktechpost.com/feed",
            "https://www.microsoft.com/en-us/research/feed/",
            "https://news.mit.edu/topic/mitmachine-learning-rss.xml",
            "https://www.technologyreview.com/feed/",
            "https://www.newscientist.com/subject/technology/feed/",
            "https://phys.org/rss-feed/technology-news/machine-learning-ai/",
            "https://techxplore.com/rss-feed/machine-learning-ai-news/",
            "https://www.assemblyai.com/blog/rss/",
            "https://nicholas.carlini.com/writing/feed.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            "https://www.oneusefulthing.org/feed",
            "https://blog.paperspace.com/rss/",
            "https://petapixel.com/feed",
            "https://erichartford.com/rss.xml",
            "https://minimaxir.com/post/index.xml",
            "https://api.quantamagazine.org/feed",
            "https://medium.com/feed/radix-ai-blog",
            "https://feeds.feedburner.com/RBloggers",
            "https://replicate.com/blog/rss",
            "https://notes.replicatecodex.com/rss/",
            "https://restofworld.org/feed/latest",
            "https://tech.eu/category/robotics/feed",
            "http://rss.sciam.com/ScientificAmerican-Global",
            "https://www.semianalysis.com/feed",
            "https://www.siliconrepublic.com/feed",
            "https://stackoverflow.blog/feed/",
            "https://arxiv.org/rss/stat.ML",
            "https://medium.com/feed/@netflixtechblog",
            "https://medium.com/feed/@odsc",
            "https://syncedreview.com/feed",
            "https://synthedia.substack.com/feed",
            "https://techcrunch.com/feed/",
            "https://www.techmeme.com/feed.xml",
            "https://techmonitor.ai/feed",
            "https://www.reutersagency.com/feed/?best-topics=tech",
            "https://www.techspot.com/backend.xml",
            "https://bdtechtalks.com/feed/",
            "https://thealgorithmicbridge.substack.com/feed",
            "https://the-decoder.com/feed/",
            "https://thegradient.pub/rss/",
            "https://www.theintrinsicperspective.com/feed/",
            "https://thenewstack.io/feed",
            "https://thenextweb.com/neural/feed",
            "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml",
            "https://thesequence.substack.com/feed",
            "https://www.thestack.technology/latest/rss/",
            "https://blog.tensorflow.org/feeds/posts/default?alt=rss",
            "https://www.thetradenews.com/feed/",
            "http://feeds.libsyn.com/102459/rss",
            "https://pub.towardsai.net/feed",
            "https://towardsdatascience.com/feed",
            "https://unwindai.substack.com/feed",
            "https://visualstudiomagazine.com/rss-feeds/news.aspx",
            "https://voicebot.ai/feed/",
            "https://wandb.ai/fully-connected/rss.xml",
            "https://blogs.windows.com/feed",
            "https://blog.wolfram.com/feed/",
            "https://aihub.org/feed?cat=-473",
            "https://aiandbanking.libsyn.com/rss",
            "https://feeds.blubrry.com/feeds/aitoday.xml",
            "https://feeds.acast.com/public/shows/e421d786-ec36-4148-aa99-7a3b2928a779",
            "https://datascienceathome.com/feed.xml",
            "https://dataskeptic.libsyn.com/rss",
            "https://datastori.es/feed/",
            "https://aneyeonai.libsyn.com/rss",
            "https://feeds.captivate.fm/gradient-dissent/",
            "https://feed.podbean.com/hdsr/feed.xml",
            "http://feeds.soundcloud.com/users/soundcloud:users:306749289/sounds.rss",
            "http://nssdeviations.com/rss",
            "https://feeds.transistor.fm/postgres-fm",
            "https://changelog.com/practicalai/feed",
            "http://lexisnexisbis.libsyn.com/rss",
            "https://talkpython.fm/episodes/rss",
            "https://feeds.libsyn.com/468519/rss",
            "http://feeds.soundcloud.com/users/soundcloud:users:264034133/sounds.rss",
            "https://feeds.transistor.fm/the-data-engineering-show",
            "https://thedataexchange.media/feed/",
            "https://feeds.megaphone.fm/marketingai",
            "https://twimlai.com/feed",
            "https://feeds.transistor.fm/this-day-in-ai",
        ]
    )
    
    # API endpoints
    arxiv_url: str = Field(default="http://export.arxiv.org/api/query?")
    github_python_url: str = Field(
        default="https://github.com/trending/python?since=daily&spoken_language_code=en"
    )
    
    github_javascript_url: str = Field(
        default="https://github.com/trending/javascript?since=daily&spoken_language_code=en"
    )
    
    # Content processing settings
    similarity_threshold: float = Field(default=0.6)
    
    # Sentiment analysis settings
    sentiment: SentimentConfig = Field(default_factory=SentimentConfig)
    
    @property
    def CURATOR_CONFIG(self) -> Dict[str, Any]:
        """
        Returns the configuration in the format expected by the curator.
        This maintains backward compatibility with the original dict structure.
        """
        return {
            'rss_feeds': self.rss_feeds,
            'arxiv_url': self.arxiv_url,
            'github_python_url': self.github_python_url,
            'github_javascript_url': self.github_javascript_url,
            'similarity_threshold': self.similarity_threshold,
            'sentiment': {
                'type': self.sentiment.type,
                'language': self.sentiment.language
            }
        }
    
    class Config:
        env_prefix = "APP_"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings class.
    Using lru_cache for creating a singleton instance.
    """
    return Settings()

# For backward compatibility
CURATOR_CONFIG = get_settings().CURATOR_CONFIG

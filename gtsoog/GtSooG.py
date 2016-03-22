from sqlalchemy.orm.exc import NoResultFound

from model import DB
from model.objects.Repository import Repository
from model.objects.IssueTracking import IssueTracking, TYPE_GITHUB
from repository.RepositoryMiner import RepositoryMiner
from issues import IssueScanner
from utils import Log
import argparse
import configparser

"""
░░░░░░░░░▄░░░░░░░░░░░░░░▄
░░░░░░░░▌▒█░░░░░░░░░░░▄▀▒▌    GTSOOG!
░░░░░░░░▌▒▒█░░░░░░░░▄▀▒▒▒▐
░░░░░░░▐▄▀▒▒▀▀▀▀▄▄▄▀▒▒▒▒▒▐     very git
░░░░░▄▄▀▒░▒▒▒▒▒▒▒▒▒█▒▒▄█▒▐  much analyze
░░░▄▀▒▒▒░░░▒▒▒░░░▒▒▒▀██▀▒▌
░░▐▒▒▒▄▄▒▒▒▒░░░▒▒▒▒▒▒▒▀▄▒▒▌     wow
░░▌░░▌█▀▒▒▒▒▒▄▀█▄▒▒▒▒▒▒▒█▒▐
░▐░░░▒▒▒▒▒▒▒▒▌██▀▒▒░░░▒▒▒▀▄▌
░▌░▒▄██▄▒▒▒▒▒▒▒▒▒░░░░░░▒▒▒▒▌
▌▒▀▐▄█▄█▌▄░▀▒▒░░░░░░░░░░▒▒▒▐
▐▒▒▐▀▐▀▒░▄▄▒▄▒▒▒▒▒▒░▒░▒░▒▒▒▒▌
▐▒▒▒▀▀▄▄▒▒▒▄▒▒▒▒▒▒▒▒░▒░▒░▒▒▐
░▌▒▒▒▒▒▒▀▀▀▒▒▒▒▒▒░▒░▒░▒░▒▒▒▌
░▐▒▒▒▒▒▒▒▒▒▒▒▒▒▒░▒░▒░▒▒▄▒▒▐
░░▀▄▒▒▒▒▒▒▒▒▒▒▒░▒░▒░▒▄▒▒▒▒▌
░░░░▀▄▒▒▒▒▒▒▒▒▒▒▄▄▄▀▒▒▒▒▄▀
░░░░░░▀▄▄▄▄▄▄▀▀▀▒▒▒▒▒▄▄▀
░░░░░░░░░▒▒▒▒▒▒▒▒▒▒▀▀
"""


# TODO: find better place for this function
def assign_issue_tracking(repository_id, issue_tracking_type, url, username=None, password=None):
    db_session = DB.create_session()
    query = db_session.query(Repository).filter(Repository.id == repository_id)
    try:
        repository = query.one()
    except NoResultFound:
        Log.error("No Repository found with id " + str(repository_id))
        db_session.close()
        return

    if repository.issueTracking is not None:
        Log.error("Repository with id " + str(repository_id) + "already has an issue tracker assigned")
        db_session.close()
        return

    issue_tracking = IssueTracking(
        repository=repository,
        type=issue_tracking_type,
        url=url,
        username=username,
        password=password
    )
    db_session.add(issue_tracking)

    repository.issueTracking = issue_tracking
    db_session.commit()

    db_session.close()


def main():

    parser = argparse.ArgumentParser(description='GtSoog - git data miner')
    parser.add_argument('-f', action="store", dest="config_file", help='Specify config file')
    args = parser.parse_args()
    config_file = args.config_file

    if config_file:
        config = configparser.ConfigParser()
        config.read(config_file)

        try:
            repository_url = config['GIT']['RepositoryURL']
        except KeyError:
            raise EnvironmentError('Repository URL is missing in config file')

    DB.create_db()

    miner = RepositoryMiner(repository_url)

    assign_issue_tracking(
        1,
        str(TYPE_GITHUB),
        "github.engineering.zhaw.ch/api/v3/repos/mekesyac/LED-Cube-Prototyper"
    )
    IssueScanner.scan_for_repository(1)


main()

"""
                       P*,
                       F :9
                E.    $  :!?
                F'M:  $   :!#.,
                >':!L*"       .`P*
                L   :         .  ~M4<(*
                 r /:         '!   ! `!!<.^"*
               ,"  ~.       9: !.  !  `M !!!!  "
              F   ~'!  :    !! `! :!:  X; `~`!:4x *
              F/       /HL  !!  ~ !!!   M> \ X: M M
             F/        MM$R!.     !~   :~!  >'M:?L4M
            F~    :::  X!@!`Mk          ~`~ ' !M ! !
          .\MX:!!!!!M8X!   XRMi         '  \ ! !>' '
          .M$!!! ~!!HMRM M$RMMMM:             ~'!
          .$M!!!   -=:^~MRMMMMMM!!:            )(>
          4RM!!   @  XM$MMMMMMM!\~!:
         :$MMM!   \!~\M$RMMMMMMMX >~MH   !!..
         :MMMM!:!!!XM8$$MMMMMMMMX>` !$8x  !!!!`:!
        F$8$MMX!!!!MMMMMMMMMMMMM!> ! !$$M  !!!!.!!>
       F$$$$MMM!!!!MMMMMMMMMMMM!!~ :  !R$M  !!!X !Xh
      *@$$$$$M!!!!?!'!MM!M!XMM!!!  !   !?RM '!!M! ~M
     68$$$$$$!~~~~` !!!!!!!!!!!!~       !!?X `!MX  `
     d$$$$$$X!X!~   `!!!!!!!!!!~ :`',    !!!! `!!X
    )MMM$$$MM!XHHM$X> `!!!!!~~  :    L   `!!!! '!!!
   \MMMM$$RMMMMM$$R~          .d      r    !!!   !!.
  FXMMMMMMMMM!?M?!       uuud`         L    !!!   !!
 $:MM$MMMMMXXX!!  <    .`               b    `!>  !!
 PX!9$MMMM$$$WMMM~    @                  N    !!.  .
l ~ M$MMM$$$$$!!   .d`                    &   !!! .!
F  . M$XM$$$$R.- u`                        k   ~!!!!
  MR~ $>X$$ :> z`                           L   `!!!
k     ? @$ X:'`                              >    `!
 k ~! !:! '$R:                               `.    !
  L       !#~@                                 k   '
   `c...  z           Hoooorse                  .
                                                  k
"""

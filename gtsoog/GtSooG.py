#!/usr/bin/python
# coding=utf-8
from issues import IssueScanner
from model import DB
from repository.RepositoryMiner import RepositoryMiner
from utils import Config
from utils import Log


def main():
    cli_args = Config.parse_arguments()

    # A config file must be provided, or else nothing will work.
    if not hasattr(cli_args, 'config_file') or not cli_args.config_file:
        Log.error("A config file must be specified!")
        return
    Config.parse_config(cli_args.config_file)

    Log.config()

    Log.info("Started. Creating database")
    DB.create_db()

    db_session = DB.create_session()

    miner = RepositoryMiner(
        Config.repository_path,
        db_session=db_session,
        branch=Config.repository_branch
    )
    repository = miner.repository_orm

    IssueScanner.assign_issue_tracking(
        repository,
        Config.issue_tracking_system,
        Config.issue_tracking_url,
        Config.issue_tracking_username,
        Config.issue_tracking_password, db_session=db_session)

    IssueScanner.scan_for_repository(repository)
    db_session.close()


main()

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
